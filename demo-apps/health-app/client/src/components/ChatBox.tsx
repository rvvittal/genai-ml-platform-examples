import { motion } from "motion/react";
import { cn } from "../utils/tailwind";
import ChatMessage from "./ChatMessage";
import ChatRow from "./ChatRow";
import ToolDisplay, { availableTools } from "./tools/ToolDisplay";
import { Event } from '../types';
import { useCallback, useEffect, useRef, useState } from "react";
import { BotLLMTextData, LLMFunctionCallData, RTVIEvent, TranscriptData } from "@pipecat-ai/client-js";
import { useRTVIClientEvent } from "@pipecat-ai/client-react";

export default function ChatBox() {
  const [messages, setMessages] = useState<Event[]>([]);
  const [messageTimeout, setMessageTimeout] = useState<ReturnType<typeof setTimeout> | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const addToolResult = useCallback((toolId: string, invocationId: string, payload: any) => {
    setMessages(prev => [
      ...prev,
      {
        type: "tool",
        id: Date.now().toString(),
        data: {
          toolId: toolId,
          invocationId: invocationId,
          payload
        },
        sender: 'assistant',
        timestamp: new Date()
      }
    ]);
  }, []);

  useRTVIClientEvent(
    RTVIEvent.LLMFunctionCall,
    useCallback(
      (data: LLMFunctionCallData) => {
        console.log('LLMFunctionCall:', data);
        if (Object.keys(availableTools).includes(data.function_name) && data.result && (data.result as (undefined | { success: boolean }))?.success === true) {
          const additionCheck = availableTools[data.function_name];
          if (additionCheck(data.result)) {
            addToolResult(data.function_name, data.tool_call_id, data.result);
          }
        }
      },
      [addToolResult]
    )
  );


  // Clear timeout when component unmounts
  useEffect(() => {
    return () => {
      if (messageTimeout) {
        clearTimeout(messageTimeout);
      }
    };
  }, [messageTimeout]);

  const addMessage = useCallback((text: string, sender: 'user' | 'assistant') => {
    // Clear any existing timeout
    if (messageTimeout) {
      clearTimeout(messageTimeout);
      setMessageTimeout(null);
    }

    setMessages(prev => {
      // Check if the last message was from the same sender
      const lastMessage = prev[prev.length - 1];

      // Check if the last message is from the same sender and is a text message (not a tool/widget)
      // This naturally ensures no widgets were added after the last message, as the last item
      // in the messages array would be the widget, not a message from this sender
      const isLastMessageFromSameSender = lastMessage &&
        lastMessage.sender === sender &&
        lastMessage.type === 'message';

      // If conditions are met, update the existing message
      if (isLastMessageFromSameSender) {
        // If from same sender, combine messages
        const updatedMessages = [...prev];

        // Combine with proper spacing - if last char is already 
        // a punctuation, just add a space, otherwise add a proper separator
        const lastChar = lastMessage.data.text.trim().slice(-1);
        const punctuation = ['.', '!', '?', ',', ':', ';'];
        let combinedText;

        if (punctuation.includes(lastChar)) {
          combinedText = `${lastMessage.data.text.trim()} ${text.trim()}`;
        } else {
          combinedText = `${lastMessage.data.text.trim()}. ${text.trim()}`;
        }

        updatedMessages[prev.length - 1] = {
          ...lastMessage,
          type: 'message',
          data: {
            text: combinedText,
          },
          timestamp: new Date() // Update timestamp to current time
        };
        return updatedMessages;
      } else {
        // If from different sender or first message, add new message
        return [
          ...prev,
          {
            type: 'message',
            id: Date.now().toString(),
            data: {
              text: text.trim(),
            },
            sender,
            timestamp: new Date()
          }
        ];
      }
    });
  }, [messageTimeout]);

  // User transcript handler - only handles capturing the text, not the speaking state
  useRTVIClientEvent(
    RTVIEvent.UserTranscript,
    useCallback(
      (data: TranscriptData) => {
        // Only add final transcripts
        if (data.final && data.text !== "ready") {
          console.log('User Transcript:', data);

          // Immediately add message without delay
          addMessage(data.text, 'user');
        }
      },
      [addMessage]
    )
  );

  // Bot transcript handler - only for capturing text
  useRTVIClientEvent(
    RTVIEvent.BotTranscript,
    useCallback(
      (data: BotLLMTextData) => {
        console.log('Bot Transcript:', data);
        // Only add message if there's actual content
        if (data.text.trim() !== '') {
          // Add bot's message to chat immediately
          addMessage(data.text, 'assistant');
        }
      },
      [addMessage]
    )
  );


  // Scroll to bottom when messages change
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  return (
    <div className="flex-1 overflow-auto py-4">
      <div className="flex gap-2 flex-col">
        {messages.map((message, idx) => (
          <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} key={message.id} className={cn({ 'mt-6': !(idx > 0 && messages[idx - 1].sender === message.sender) })}>
            <ChatRow sender={message.sender} hideIcon={idx > 0 && messages[idx - 1].sender === message.sender} timestamp={message.timestamp}>
              {
                message.type === 'message' ?
                  <ChatMessage message={message.data.text} sender={message.sender} />
                  : <ToolDisplay type={message.data.toolId} timestamp={message.timestamp} data={message.data.payload} />
              }
            </ChatRow>
          </motion.div>
        ))}
      </div>
      <div ref={messagesEndRef} />
    </div>
  )
}