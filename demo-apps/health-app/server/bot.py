#
# Copyright (c) 2025, Daily
#
# SPDX-License-Identifier: BSD 2-Clause License
#

"""
AI Health Assistant Bot

This module implements the main bot logic for the AI Health Assistant.
It uses Pipecat framework for real-time voice interaction, AWS Nova Sonic for LLM services,
and Daily for audio/video transportation.

The bot can:
- Engage in natural voice conversations about health concerns
- Ask follow-up questions about symptoms
- Query a health knowledge base
- Help users book medical appointments
- Provide appointment scheduling assistance
"""

import aiohttp
import asyncio
import os
import tools
from runner import configure
from prompt_manager import PromptManager

from dotenv import load_dotenv
from loguru import logger
from pipecat.audio.vad.silero import SileroVADAnalyzer
from pipecat.audio.vad.vad_analyzer import VADParams
from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.runner import PipelineRunner
from pipecat.pipeline.task import PipelineParams, PipelineTask
from pipecat.processors.aggregators.openai_llm_context import OpenAILLMContext
from pipecat.processors.frameworks.rtvi import RTVIConfig, RTVIObserver, RTVIProcessor, RTVIObserverParams
from pipecat.services.aws_nova_sonic.aws import AWSNovaSonicLLMService, Params
from pipecat.transports.services.daily import DailyParams, DailyTransport

# Load environment variables from .env file
load_dotenv(override=True)


async def main():
    """
    Main function that sets up and runs the AI Health Assistant bot.
    
    This function:
    1. Configures the Daily transport for audio/video
    2. Sets up the AWS Nova Sonic LLM service
    3. Registers health assistant functions
    4. Creates the conversation pipeline
    5. Handles client connection events
    """
    logger.info("Starting AI Health Assistant bot")

    async with aiohttp.ClientSession() as session:
        # Configure Daily room and get connection details
        (room_url, token) = await configure(session)

        # Set up Daily transport with audio/video parameters
        # This handles the real-time audio/video communication with clients
        transport = DailyTransport(
            room_url,
            token,
            "Health Assistant",  # Bot display name
            DailyParams(
                audio_in_enabled=True,   # Enable microphone input
                audio_out_enabled=True,  # Enable speaker output
                video_out_enabled=False, # Disable video output (audio-only bot)
                video_out_width=1024,    # Video dimensions (unused since video disabled)
                video_out_height=576,
                # Voice Activity Detection (VAD) configuration
                # Helps detect when user stops speaking
                vad_analyzer=SileroVADAnalyzer(params=VADParams(
                    stop_secs=0.2  # Wait 0.2 seconds of silence before processing
                )),
                # Note: transcription_enabled is commented out - can be enabled for debugging
                # transcription_enabled=True,
            ),
        )

        # Initialize the prompt manager with system instructions
        # Override date for demo purposes - in production, remove override_date parameter
        prompt_manager = PromptManager(override_date="Jun 5, 2025")
        system_instruction = prompt_manager.create_system_instruction()

        # Configure AWS Nova Sonic LLM service
        # This service handles natural language understanding and generation
        llm = AWSNovaSonicLLMService(
            secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
            access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
            region=os.getenv("AWS_REGION"),
            voice_id="amy",  # Available voices: matthew (US), tiffany (US), amy (GB)
            params=Params(
                temperature=0.0,  # Low temperature for consistent, factual responses
                top_p=0.8        # Nucleus sampling parameter
            )
        )
        
        # Register health assistant functions that the LLM can call
        # These functions provide the bot with capabilities beyond conversation
        
        # Appointment booking functionality
        llm.register_function("book_appointment", tools.book_appointment)
        
        # Health knowledge base querying
        llm.register_function("query_health_kb", tools.query_health_kb)
        
        # Calendar and scheduling functions
        llm.register_function("get_non_clashing_slots", tools.get_non_clashing_slots)
        llm.register_function("get_all_doctors", tools.get_all_doctors)
        
        # Note: Additional functions are available but commented out for demo simplicity
        # llm.register_function("summarize_symptoms", tools.summarize_symptoms)
        # llm.register_function("get_available_slots", tools.get_available_slots)
        # llm.register_function("suggest_earliest_appointment", tools.suggest_earliest_appointment)

        # Create conversation context with system instructions and available tools
        context = OpenAILLMContext(
            messages=[
                {"role": "system", "content": f"{system_instruction}"},
            ],
            tools=tools.tools_schema,  # Schema defining available function calls
        )
        context_aggregator = llm.create_context_aggregator(context)

        # RTVI (Real-Time Voice Interface) processor for client UI integration
        # This enables the web client to receive structured data and events
        rtvi = RTVIProcessor(config=RTVIConfig(config=[]))

        # Create the processing pipeline
        # Data flows: input -> context -> rtvi -> llm -> output -> context
        pipeline = Pipeline(
            [
                transport.input(),           # Receive audio from client
                context_aggregator.user(),   # Process user input and maintain context
                rtvi,                        # Handle RTVI events for client UI
                llm,                         # Generate LLM responses and function calls
                transport.output(),          # Send audio back to client
                context_aggregator.assistant(), # Process assistant responses and maintain context
            ]
        )

        # Configure the pipeline task with performance and monitoring settings
        task = PipelineTask(
            pipeline,
            params=PipelineParams(
                allow_interruptions=True,        # Allow users to interrupt the bot
                enable_metrics=True,             # Enable performance metrics
                enable_usage_metrics=True,       # Enable usage tracking
                report_only_initial_ttfb=True,   # Time to first byte reporting
                observers=[
                    # RTVI observer for handling client events and function call results
                    RTVIObserver(rtvi, params=RTVIObserverParams(
                        function_call_result_enabled=True  # Send function results to client
                        )
                    ),
                ],
            ),
        )

        # Event handlers for client lifecycle management
        
        @rtvi.event_handler("on_client_ready")
        async def on_client_ready(rtvi):
            """
            Handle client ready event.
            Called when the web client has successfully connected and is ready to interact.
            """
            logger.info("Pipecat client ready.")
            await rtvi.set_bot_ready()
            # Initialize conversation context
            await task.queue_frames([context_aggregator.user().get_context_frame()])

        @transport.event_handler("on_first_participant_joined")
        async def on_first_participant_joined(transport, participant):
            """
            Handle first participant joining the Daily room.
            Sets up transcription and triggers the initial assistant response.
            """
            logger.info("Client connected")
            # Enable transcription for the participant
            await transport.capture_participant_transcription(participant["id"])
            
            # Trigger initial assistant response
            # Note: This is a specific requirement for AWS Nova Sonic
            # The system instruction should include text that responds to this trigger
            await llm.trigger_assistant_response()

        @transport.event_handler("on_participant_left")
        async def on_participant_left(transport, participant, reason):
            """
            Handle participant leaving the Daily room.
            Cleans up the conversation and cancels the pipeline task.
            """
            logger.info(f"Client disconnected: {reason}")
            await task.cancel()

        # Start the pipeline runner
        # This will run until the task is cancelled or an error occurs
        runner = PipelineRunner(handle_sigint=False)
        await runner.run(task)


if __name__ == "__main__":
    # Run the main function in an asyncio event loop
    asyncio.run(main())