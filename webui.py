# python webui.py --ip 127.0.0.1 --port 7788

import pdb
import logging

from dotenv import load_dotenv

load_dotenv()
import os
import glob
import asyncio
import argparse
import os

logger = logging.getLogger(__name__)

import gradio as gr

from browser_use.agent.service import Agent
from playwright.async_api import async_playwright
from browser_use.browser.browser import Browser, BrowserConfig
from browser_use.browser.context import (
    BrowserContextConfig,
    BrowserContextWindowSize,
)
from langchain_google_genai import ChatGoogleGenerativeAI
from playwright.async_api import async_playwright
from src.utils.agent_state import AgentState

from src.utils import utils
from src.agent.custom_agent import CustomAgent
from src.browser.custom_browser import CustomBrowser
from src.agent.custom_prompts import CustomSystemPrompt, CustomAgentMessagePrompt
from src.browser.custom_context import BrowserContextConfig, CustomBrowserContext
from src.controller.custom_controller import CustomController
from gradio.themes import Citrus, Default, Glass, Monochrome, Ocean, Origin, Soft, Base
from src.utils.default_config_settings import default_config, load_config_from_file, save_config_to_file, save_current_config, update_ui_from_config
from src.utils.utils import update_model_dropdown, get_latest_files, capture_screenshot


# Global variables for persistence
_global_browser = None
_global_browser_context = None

# Create the global agent state instance
_global_agent_state = AgentState()

async def stop_agent():
    """Request the agent to stop and update UI with enhanced feedback"""
    global _global_agent_state, _global_browser_context, _global_browser

    try:
        # Request stop
        _global_agent_state.request_stop()

        # Update UI immediately
        message = "Stop requested - the agent will halt at the next safe point"
        logger.info(f"🛑 {message}")

        # Return UI updates
        return (
            message,                                        # errors_output
            gr.update(value="Stopping...", interactive=False),  # stop_button
            gr.update(interactive=False),                      # run_button
        )
    except Exception as e:
        error_msg = f"Error during stop: {str(e)}"
        logger.error(error_msg)
        return (
            error_msg,
            gr.update(value="Stop", interactive=True),
            gr.update(interactive=True)
        )

async def run_browser_agent(
        agent_type,
        llm_provider,
        llm_model_name,
        llm_temperature,
        llm_base_url,
        llm_api_key,
        use_own_browser,
        keep_browser_open,
        headless,
        disable_security,
        window_w,
        window_h,
        save_recording_path,
        save_agent_history_path,
        save_trace_path,
        enable_recording,
        task,
        add_infos,
        max_steps,
        use_vision,
        max_actions_per_step,
        tool_calling_method
):
    global _global_agent_state
    _global_agent_state.clear_stop()  # Clear any previous stop requests

    try:
        # Disable recording if the checkbox is unchecked
        if not enable_recording:
            save_recording_path = None

        # Ensure the recording directory exists if recording is enabled
        if save_recording_path:
            os.makedirs(save_recording_path, exist_ok=True)

        # Get the list of existing videos before the agent runs
        existing_videos = set()
        if save_recording_path:
            existing_videos = set(
                glob.glob(os.path.join(save_recording_path, "*.[mM][pP]4"))
                + glob.glob(os.path.join(save_recording_path, "*.[wW][eE][bB][mM]"))
            )

        # Run the agent
        llm = utils.get_llm_model(
            provider=llm_provider,
            model_name=llm_model_name,
            temperature=llm_temperature,
            base_url=llm_base_url,
            api_key=llm_api_key,
        )
        if agent_type == "org":
            final_result, errors, model_actions, model_thoughts, trace_file, history_file = await run_org_agent(
                llm=llm,
                use_own_browser=use_own_browser,
                keep_browser_open=keep_browser_open,
                headless=headless,
                disable_security=disable_security,
                window_w=window_w,
                window_h=window_h,
                save_recording_path=save_recording_path,
                save_agent_history_path=save_agent_history_path,
                save_trace_path=save_trace_path,
                task=task,
                max_steps=max_steps,
                use_vision=use_vision,
                max_actions_per_step=max_actions_per_step,
                tool_calling_method=tool_calling_method
            )
        elif agent_type == "custom":
            final_result, errors, model_actions, model_thoughts, trace_file, history_file = await run_custom_agent(
                llm=llm,
                use_own_browser=use_own_browser,
                keep_browser_open=keep_browser_open,
                headless=headless,
                disable_security=disable_security,
                window_w=window_w,
                window_h=window_h,
                save_recording_path=save_recording_path,
                save_agent_history_path=save_agent_history_path,
                save_trace_path=save_trace_path,
                task=task,
                add_infos=add_infos,
                max_steps=max_steps,
                use_vision=use_vision,
                max_actions_per_step=max_actions_per_step,
                tool_calling_method=tool_calling_method
            )
        else:
            raise ValueError(f"Invalid agent type: {agent_type}")

        # Get the list of videos after the agent runs (if recording is enabled)
        latest_video = None
        if save_recording_path:
            new_videos = set(
                glob.glob(os.path.join(save_recording_path, "*.[mM][pP]4"))
                + glob.glob(os.path.join(save_recording_path, "*.[wW][eE][bB][mM]"))
            )
            if new_videos - existing_videos:
                latest_video = list(new_videos - existing_videos)[0]  # Get the first new video

        return (
            final_result,
            errors,
            model_actions,
            model_thoughts,
            latest_video,
            trace_file,
            history_file,
            gr.update(value="Stop", interactive=True),  # Re-enable stop button
            gr.update(interactive=True)    # Re-enable run button
        )

    except gr.Error:
        raise

    except Exception as e:
        import traceback
        traceback.print_exc()
        errors = str(e) + "\n" + traceback.format_exc()
        return (
            '',                                         # final_result
            errors,                                     # errors
            '',                                         # model_actions
            '',                                         # model_thoughts
            None,                                       # latest_video
            None,                                       # history_file
            None,                                       # trace_file
            gr.update(value="Stop", interactive=True),  # Re-enable stop button
            gr.update(interactive=True)    # Re-enable run button
        )


async def run_org_agent(
        llm,
        use_own_browser,
        keep_browser_open,
        headless,
        disable_security,
        window_w,
        window_h,
        save_recording_path,
        save_agent_history_path,
        save_trace_path,
        task,
        max_steps,
        use_vision,
        max_actions_per_step,
        tool_calling_method
):
    try:
        global _global_browser, _global_browser_context, _global_agent_state
        
        # Clear any previous stop request
        _global_agent_state.clear_stop()

        extra_chromium_args = [f"--window-size={window_w},{window_h}"]
        if use_own_browser:
            chrome_path = os.getenv("CHROME_PATH", None)
            if chrome_path == "":
                chrome_path = None
            chrome_user_data = os.getenv("CHROME_USER_DATA", None)
            if chrome_user_data:
                extra_chromium_args += [f"--user-data-dir={chrome_user_data}"]
        else:
            chrome_path = None
            
        if _global_browser is None:
            _global_browser = Browser(
                config=BrowserConfig(
                    headless=headless,
                    disable_security=disable_security,
                    chrome_instance_path=chrome_path,
                    extra_chromium_args=extra_chromium_args,
                )
            )

        if _global_browser_context is None:
            _global_browser_context = await _global_browser.new_context(
                config=BrowserContextConfig(
                    trace_path=save_trace_path if save_trace_path else None,
                    save_recording_path=save_recording_path if save_recording_path else None,
                    no_viewport=False,
                    browser_window_size=BrowserContextWindowSize(
                        width=window_w, height=window_h
                    ),
                )
            )
            
        agent = Agent(
            task=task,
            llm=llm,
            use_vision=use_vision,
            browser=_global_browser,
            browser_context=_global_browser_context,
            max_actions_per_step=max_actions_per_step,
            tool_calling_method=tool_calling_method
        )
        history = await agent.run(max_steps=max_steps)

        history_file = os.path.join(save_agent_history_path, f"{agent.agent_id}.json")
        agent.save_history(history_file)

        final_result = history.final_result()
        errors = history.errors()
        model_actions = history.model_actions()
        model_thoughts = history.model_thoughts()

        trace_file = get_latest_files(save_trace_path)

        return final_result, errors, model_actions, model_thoughts, trace_file.get('.zip'), history_file
    except Exception as e:
        import traceback
        traceback.print_exc()
        errors = str(e) + "\n" + traceback.format_exc()
        return '', errors, '', '', None, None
    finally:
        # Handle cleanup based on persistence configuration
        if not keep_browser_open:
            if _global_browser_context:
                await _global_browser_context.close()
                _global_browser_context = None

            if _global_browser:
                await _global_browser.close()
                _global_browser = None

async def run_custom_agent(
        llm,
        use_own_browser,
        keep_browser_open,
        headless,
        disable_security,
        window_w,
        window_h,
        save_recording_path,
        save_agent_history_path,
        save_trace_path,
        task,
        add_infos,
        max_steps,
        use_vision,
        max_actions_per_step,
        tool_calling_method
):
    try:
        global _global_browser, _global_browser_context, _global_agent_state

        # Clear any previous stop request
        _global_agent_state.clear_stop()

        extra_chromium_args = [f"--window-size={window_w},{window_h}"]
        if use_own_browser:
            chrome_path = os.getenv("CHROME_PATH", None)
            if chrome_path == "":
                chrome_path = None
            chrome_user_data = os.getenv("CHROME_USER_DATA", None)
            if chrome_user_data:
                extra_chromium_args += [f"--user-data-dir={chrome_user_data}"]
        else:
            chrome_path = None

        controller = CustomController()

        # Initialize global browser if needed
        if _global_browser is None:
            _global_browser = CustomBrowser(
                config=BrowserConfig(
                    headless=headless,
                    disable_security=disable_security,
                    chrome_instance_path=chrome_path,
                    extra_chromium_args=extra_chromium_args,
                )
            )

        if _global_browser_context is None:
            _global_browser_context = await _global_browser.new_context(
                config=BrowserContextConfig(
                    trace_path=save_trace_path if save_trace_path else None,
                    save_recording_path=save_recording_path if save_recording_path else None,
                    no_viewport=False,
                    browser_window_size=BrowserContextWindowSize(
                        width=window_w, height=window_h
                    ),
                )
            )
            
        # Create and run agent
        agent = CustomAgent(
            task=task,
            add_infos=add_infos,
            use_vision=use_vision,
            llm=llm,
            browser=_global_browser,
            browser_context=_global_browser_context,
            controller=controller,
            system_prompt_class=CustomSystemPrompt,
            agent_prompt_class=CustomAgentMessagePrompt,
            max_actions_per_step=max_actions_per_step,
            agent_state=_global_agent_state,
            tool_calling_method=tool_calling_method
        )
        history = await agent.run(max_steps=max_steps)

        history_file = os.path.join(save_agent_history_path, f"{agent.agent_id}.json")
        agent.save_history(history_file)

        final_result = history.final_result()
        errors = history.errors()
        model_actions = history.model_actions()
        model_thoughts = history.model_thoughts()

        trace_file = get_latest_files(save_trace_path)        

        return final_result, errors, model_actions, model_thoughts, trace_file.get('.zip'), history_file
    except Exception as e:
        import traceback
        traceback.print_exc()
        errors = str(e) + "\n" + traceback.format_exc()
        return '', errors, '', '', None, None
    finally:
        # Handle cleanup based on persistence configuration
        if not keep_browser_open:
            if _global_browser_context:
                await _global_browser_context.close()
                _global_browser_context = None

            if _global_browser:
                await _global_browser.close()
                _global_browser = None

async def run_with_stream(
    agent_type,
    llm_provider,
    llm_model_name,
    llm_temperature,
    llm_base_url,
    llm_api_key,
    use_own_browser,
    keep_browser_open,
    headless,
    disable_security,
    window_w,
    window_h,
    save_recording_path,
    save_agent_history_path,
    save_trace_path,
    enable_recording,
    task,
    add_infos,
    max_steps,
    use_vision,
    max_actions_per_step,
    tool_calling_method
):
    global _global_agent_state
    stream_vw = 80
    stream_vh = int(80 * window_h // window_w)
    if not headless:
        result = await run_browser_agent(
            agent_type=agent_type,
            llm_provider=llm_provider,
            llm_model_name=llm_model_name,
            llm_temperature=llm_temperature,
            llm_base_url=llm_base_url,
            llm_api_key=llm_api_key,
            use_own_browser=use_own_browser,
            keep_browser_open=keep_browser_open,
            headless=headless,
            disable_security=disable_security,
            window_w=window_w,
            window_h=window_h,
            save_recording_path=save_recording_path,
            save_agent_history_path=save_agent_history_path,
            save_trace_path=save_trace_path,
            enable_recording=enable_recording,
            task=task,
            add_infos=add_infos,
            max_steps=max_steps,
            use_vision=use_vision,
            max_actions_per_step=max_actions_per_step,
            tool_calling_method=tool_calling_method
        )
        # Add HTML content at the start of the result array
        html_content = f"<h1 style='width:{stream_vw}vw; height:{stream_vh}vh'>Using browser...</h1>"
        yield [html_content] + list(result)
    else:
        try:
            _global_agent_state.clear_stop()
            # Run the browser agent in the background
            agent_task = asyncio.create_task(
                run_browser_agent(
                    agent_type=agent_type,
                    llm_provider=llm_provider,
                    llm_model_name=llm_model_name,
                    llm_temperature=llm_temperature,
                    llm_base_url=llm_base_url,
                    llm_api_key=llm_api_key,
                    use_own_browser=use_own_browser,
                    keep_browser_open=keep_browser_open,
                    headless=headless,
                    disable_security=disable_security,
                    window_w=window_w,
                    window_h=window_h,
                    save_recording_path=save_recording_path,
                    save_agent_history_path=save_agent_history_path,
                    save_trace_path=save_trace_path,
                    enable_recording=enable_recording,
                    task=task,
                    add_infos=add_infos,
                    max_steps=max_steps,
                    use_vision=use_vision,
                    max_actions_per_step=max_actions_per_step,
                    tool_calling_method=tool_calling_method
                )
            )

            # Initialize values for streaming
            html_content = f"<h1 style='width:{stream_vw}vw; height:{stream_vh}vh'>Using browser...</h1>"
            final_result = errors = model_actions = model_thoughts = ""
            latest_videos = trace = history_file = None


            # Periodically update the stream while the agent task is running
            while not agent_task.done():
                try:
                    encoded_screenshot = await capture_screenshot(_global_browser_context)
                    if encoded_screenshot is not None:
                        html_content = f'<img src="data:image/jpeg;base64,{encoded_screenshot}" style="width:{stream_vw}vw; height:{stream_vh}vh ; border:1px solid #ccc;">'
                    else:
                        html_content = f"<h1 style='width:{stream_vw}vw; height:{stream_vh}vh'>Waiting for browser session...</h1>"
                except Exception as e:
                    html_content = f"<h1 style='width:{stream_vw}vw; height:{stream_vh}vh'>Waiting for browser session...</h1>"

                if _global_agent_state and _global_agent_state.is_stop_requested():
                    yield [
                        html_content,
                        final_result,
                        errors,
                        model_actions,
                        model_thoughts,
                        latest_videos,
                        trace,
                        history_file,
                        gr.update(value="Stopping...", interactive=False),  # stop_button
                        gr.update(interactive=False),  # run_button
                    ]
                    break
                else:
                    yield [
                        html_content,
                        final_result,
                        errors,
                        model_actions,
                        model_thoughts,
                        latest_videos,
                        trace,
                        history_file,
                        gr.update(value="Stop", interactive=True),  # Re-enable stop button
                        gr.update(interactive=True)  # Re-enable run button
                    ]
                await asyncio.sleep(0.05)

            # Once the agent task completes, get the results
            try:
                result = await agent_task
                final_result, errors, model_actions, model_thoughts, latest_videos, trace, history_file, stop_button, run_button = result
            except gr.Error:
                final_result = ""
                model_actions = ""
                model_thoughts = ""
                latest_videos = trace = history_file = None

            except Exception as e:
                errors = f"Agent error: {str(e)}"

            yield [
                html_content,
                final_result,
                errors,
                model_actions,
                model_thoughts,
                latest_videos,
                trace,
                history_file,
                stop_button,
                run_button
            ]

        except Exception as e:
            import traceback
            yield [
                f"<h1 style='width:{stream_vw}vw; height:{stream_vh}vh'>Waiting for browser session...</h1>",
                "",
                f"Error: {str(e)}\n{traceback.format_exc()}",
                "",
                "",
                None,
                None,
                None,
                gr.update(value="Stop", interactive=True),  # Re-enable stop button
                gr.update(interactive=True)    # Re-enable run button
            ]

# Define the theme map globally
theme_map = {
    "Default": Default(),
    "Soft": Soft(),
    "Monochrome": Monochrome(),
    "Glass": Glass(),
    "Origin": Origin(),
    "Citrus": Citrus(),
    "Ocean": Ocean(),
    "Base": Base()
}

async def close_global_browser():
    global _global_browser, _global_browser_context

    if _global_browser_context:
        await _global_browser_context.close()
        _global_browser_context = None

    if _global_browser:
        await _global_browser.close()
        _global_browser = None

def create_ui(config, theme_name="Ocean"):
    css = """
    .gradio-container {
        max-width: 1200px !important;
        margin: auto !important;
        padding-top: 20px !important;
    }
    .header-text {
        text-align: center;
        margin-bottom: 30px;
    }
    .theme-section {
        margin-bottom: 20px;
        padding: 15px;
        border-radius: 10px;
    }
    """

    with gr.Blocks(
            title="Browser Use WebUI", theme=theme_map[theme_name], css=css
    ) as demo:
        with gr.Row():
            gr.Markdown(
                """
                # 🌐 Browser Use WebUI
                ### Controle seu navegador com assistência de IA
                """,
                elem_classes=["header-text"],
            )

        with gr.Tabs() as tabs:
            with gr.TabItem("⚙️ Configurações do Agente", id=1):
                with gr.Group():
                    agent_type = gr.Radio(
                        ["org", "custom"],
                        label="Tipo de Agente",
                        value=config['agent_type'],
                        info="Selecione o tipo de agente a ser usado",
                    )
                    with gr.Column():
                        max_steps = gr.Slider(
                            minimum=1,
                            maximum=200,
                            value=config['max_steps'],
                            step=1,
                            label="Máximo de Passos",
                            info="Número máximo de passos que o agente executará",
                        )
                        max_actions_per_step = gr.Slider(
                            minimum=1,
                            maximum=20,
                            value=config['max_actions_per_step'],
                            step=1,
                            label="Máximo de Ações por Passo",
                            info="Número máximo de ações que o agente executará por passo",
                        )
                    with gr.Column():
                        use_vision = gr.Checkbox(
                            label="Usar Visão",
                            value=config['use_vision'],
                            info="Ativar capacidades de processamento visual",
                        )
                        tool_calling_method = gr.Dropdown(
                            label="Método de Chamada de Ferramenta",
                            value=config['tool_calling_method'],
                            interactive=True,
                            allow_custom_value=True,  # Permitir que os usuários insiram nomes de modelos personalizados
                            choices=["auto", "json_schema", "function_calling"],
                            info="Nome da Função de Chamada de Ferramenta",
                            visible=False
                        )

            with gr.TabItem("🔧 Configuração do LLM", id=2):
                with gr.Group():
                    llm_provider = gr.Dropdown(
                        choices=[provider for provider,model in utils.model_names.items()],
                        label="Provedor do LLM",
                        value=config['llm_provider'],
                        info="Selecione seu provedor de modelo de linguagem preferido"
                    )
                    llm_model_name = gr.Dropdown(
                        label="Nome do Modelo",
                        choices=utils.model_names['openai'],
                        value=config['llm_model_name'],
                        interactive=True,
                        allow_custom_value=True,  # Permitir que os usuários insiram nomes de modelos personalizados
                        info="Selecione um modelo do menu suspenso ou digite um nome de modelo personalizado"
                    )
                    llm_temperature = gr.Slider(
                        minimum=0.0,
                        maximum=2.0,
                        value=config['llm_temperature'],
                        step=0.1,
                        label="Temperatura",
                        info="Controla a aleatoriedade nas saídas do modelo"
                    )
                    with gr.Row():
                        llm_base_url = gr.Textbox(
                            label="URL Base",
                            value=config['llm_base_url'],
                            info="URL do endpoint da API (se necessário)"
                        )
                        llm_api_key = gr.Textbox(
                            label="Chave da API",
                            type="password",
                            value=config['llm_api_key'],
                            info="Sua chave de API (deixe em branco para usar .env)"
                        )

            with gr.TabItem("🌐 Configurações do Navegador", id=3):
                with gr.Group():
                    with gr.Row():
                        use_own_browser = gr.Checkbox(
                            label="Usar Próprio Navegador",
                            value=config['use_own_browser'],
                            info="Usar sua instância existente do navegador",
                        )
                        keep_browser_open = gr.Checkbox(
                            label="Manter Navegador Aberto",
                            value=config['keep_browser_open'],
                            info="Manter o navegador aberto entre tarefas",
                        )
                        headless = gr.Checkbox(
                            label="Modo Sem Cabeça",
                            value=config['headless'],
                            info="Executar o navegador sem interface gráfica",
                        )
                        disable_security = gr.Checkbox(
                            label="Desativar Segurança",
                            value=config['disable_security'],
                            info="Desativar recursos de segurança do navegador",
                        )
                        enable_recording = gr.Checkbox(
                            label="Ativar Gravação",
                            value=config['enable_recording'],
                            info="Ativar a gravação das sessões do navegador",
                        )

                    with gr.Row():
                        window_w = gr.Number(
                            label="Largura da Janela",
                            value=config['window_w'],
                            info="Largura da janela do navegador",
                        )
                        window_h = gr.Number(
                            label="Altura da Janela",
                            value=config['window_h'],
                            info="Altura da janela do navegador",
                        )

                    save_recording_path = gr.Textbox(
                        label="Caminho da Gravação",
                        placeholder="e.g. ./tmp/record_videos",
                        value=config['save_recording_path'],
                        info="Caminho para salvar as gravações do navegador",
                        interactive=True,  # Permitir edição apenas se a gravação estiver ativada
                    )

                    save_trace_path = gr.Textbox(
                        label="Caminho do Traçado",
                        placeholder="e.g. ./tmp/traces",
                        value=config['save_trace_path'],
                        info="Caminho para salvar os traçados do agente",
                        interactive=True,
                    )

                    save_agent_history_path = gr.Textbox(
                        label="Caminho para Salvar o Histórico do Agente",
                        placeholder="e.g., ./tmp/agent_history",
                        value=config['save_agent_history_path'],
                        info="Especifique o diretório onde o histórico do agente deve ser salvo.",
                        interactive=True,
                    )

            with gr.TabItem("🤖 Executar Agente", id=4):
                task = gr.Textbox(
                    label="Descrição da Tarefa",
                    lines=4,
                    placeholder="Insira sua tarefa aqui...",
                    value=config['task'],
                    info="Descreva o que você deseja que o agente faça",
                )
                add_infos = gr.Textbox(
                    label="Informações Adicionais",
                    lines=3,
                    placeholder="Adicione qualquer contexto ou instruções úteis...",
                    info="Dicas opcionais para ajudar o LLM a completar a tarefa",
                )

                with gr.Row():
                    run_button = gr.Button("▶️ Executar Agente", variant="primary", scale=2)
                    stop_button = gr.Button("⏹️ Parar", variant="stop", scale=1)

                with gr.Row():
                    browser_view = gr.HTML(
                        value="<h1 style='width:80vw; height:50vh'>Aguardando a sessão do navegador...</h1>",
                        label="Visualização ao Vivo do Navegador",
                )

            with gr.TabItem("📁 Configuração", id=5):
                with gr.Group():
                    config_file_input = gr.File(
                        label="Carregar Arquivo de Configuração",
                        file_types=[".pkl"],
                        interactive=True
                    )

                    load_config_button = gr.Button("Carregar Configuração Existente do Arquivo", variant="primary")
                    save_config_button = gr.Button("Salvar Configuração Atual", variant="primary")

                    config_status = gr.Textbox(
                        label="Status",
                        lines=2,
                        interactive=False
                    )

                load_config_button.click(
                    fn=update_ui_from_config,
                    inputs=[config_file_input],
                    outputs=[
                        agent_type, max_steps, max_actions_per_step, use_vision, tool_calling_method,
                        llm_provider, llm_model_name, llm_temperature, llm_base_url, llm_api_key,
                        use_own_browser, keep_browser_open, headless, disable_security, enable_recording,
                        window_w, window_h, save_recording_path, save_trace_path, save_agent_history_path,
                        task, config_status
                    ]
                )

                save_config_button.click(
                    fn=save_current_config,
                    inputs=[
                        agent_type, max_steps, max_actions_per_step, use_vision, tool_calling_method,
                        llm_provider, llm_model_name, llm_temperature, llm_base_url, llm_api_key,
                        use_own_browser, keep_browser_open, headless, disable_security,
                        enable_recording, window_w, window_h, save_recording_path, save_trace_path,
                        save_agent_history_path, task,
                    ],
                    outputs=[config_status]
                )

            with gr.TabItem("📊 Resultados", id=6):
                with gr.Group():

                    recording_display = gr.Video(label="Última Gravação")

                    gr.Markdown("### Resultados")
                    with gr.Row():
                        with gr.Column():
                            final_result_output = gr.Textbox(
                                label="Resultado Final", lines=3, show_label=True
                            )
                        with gr.Column():
                            errors_output = gr.Textbox(
                                label="Erros", lines=3, show_label=True
                            )
                    with gr.Row():
                        with gr.Column():
                            model_actions_output = gr.Textbox(
                                label="Ações do Modelo", lines=3, show_label=True
                            )
                        with gr.Column():
                            model_thoughts_output = gr.Textbox(
                                label="Pensamentos do Modelo", lines=3, show_label=True
                            )

                    trace_file = gr.File(label="Arquivo de Traçado")

                    agent_history_file = gr.File(label="Histórico do Agente")

                # Associar o evento de clique do botão de parar após a definição de errors_output
                stop_button.click(
                    fn=stop_agent,
                    inputs=[],
                    outputs=[errors_output, stop_button, run_button],
                )

                # Manipulador de clique do botão de execução
                run_button.click(
                    fn=run_with_stream,
                        inputs=[
                            agent_type, llm_provider, llm_model_name, llm_temperature, llm_base_url, llm_api_key,
                            use_own_browser, keep_browser_open, headless, disable_security, window_w, window_h,
                            save_recording_path, save_agent_history_path, save_trace_path,  # Incluir o novo caminho
                            enable_recording, task, add_infos, max_steps, use_vision, max_actions_per_step, tool_calling_method
                        ],
                    outputs=[
                        browser_view,           # Visualização do navegador
                        final_result_output,    # Resultado final
                        errors_output,          # Erros
                        model_actions_output,   # Ações do modelo
                        model_thoughts_output,  # Pensamentos do modelo
                        recording_display,      # Última gravação
                        trace_file,             # Arquivo de traçado
                        agent_history_file,     # Arquivo de histórico do agente
                        stop_button,            # Botão de parar
                        run_button              # Botão de executar
                    ],
                )

            with gr.TabItem("🎥 Gravações", id=7):
                def list_recordings(save_recording_path):
                    if not os.path.exists(save_recording_path):
                        return []

                    # Obter todos os arquivos de vídeo
                    recordings = glob.glob(os.path.join(save_recording_path, "*.[mM][pP]4")) + glob.glob(os.path.join(save_recording_path, "*.[wW][eE][bB][mM]"))

                    # Ordenar gravações por tempo de criação (mais antigas primeiro)
                    recordings.sort(key=os.path.getctime)

                    # Adicionar numeração às gravações
                    numbered_recordings = []
                    for idx, recording in enumerate(recordings, start=1):
                        filename = os.path.basename(recording)
                        numbered_recordings.append((recording, f"{idx}. {filename}"))

                    return numbered_recordings

                recordings_gallery = gr.Gallery(
                    label="Gravações",
                    value=list_recordings(config['save_recording_path']),
                    columns=3,
                    height="auto",
                    object_fit="contain"
                )

                refresh_button = gr.Button("🔄 Atualizar Gravações", variant="secondary")
                refresh_button.click(
                    fn=list_recordings,
                    inputs=save_recording_path,
                    outputs=recordings_gallery
                )

        # Anexar o callback ao dropdown do provedor do LLM
        llm_provider.change(
            lambda provider, api_key, base_url: update_model_dropdown(provider, api_key, base_url),
            inputs=[llm_provider, llm_api_key, llm_base_url],
            outputs=llm_model_name
        )

        # Adicionar isso após definir os componentes
        enable_recording.change(
            lambda enabled: gr.update(interactive=enabled),
            inputs=enable_recording,
            outputs=save_recording_path
        )

        use_own_browser.change(fn=close_global_browser)
        keep_browser_open.change(fn=close_global_browser)

    return demo

def main():
    parser = argparse.ArgumentParser(description="Interface Gráfica para Agente de Navegador")
    parser.add_argument("--ip", type=str, default="127.0.0.1", help="Endereço IP para vincular")
    parser.add_argument("--port", type=int, default=7788, help="Porta para escutar")
    parser.add_argument("--theme", type=str, default="Ocean", choices=theme_map.keys(), help="Tema a ser usado na interface")
    parser.add_argument("--dark-mode", action="store_true", help="Ativar modo escuro")
    args = parser.parse_args()

    config_dict = default_config()

    demo = create_ui(config_dict, theme_name=args.theme)
    demo.launch(server_name=args.ip, server_port=args.port)

if __name__ == '__main__':
    main()

