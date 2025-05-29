/* eslint-disable @typescript-eslint/no-explicit-any */
import { RTVIClientAudio, useRTVIClient, useRTVIClientEvent, useRTVIClientTransportState } from "@pipecat-ai/client-react";
import NavBar from "./components/NavBar";
import { cn } from "./utils/tailwind";
import { useCallback, useEffect, useState } from "react";
import { RTVIEvent } from "@pipecat-ai/client-js";
import { AgentActions } from './components/AgentActions';
import { motion, AnimatePresence } from 'motion/react';
import WelcomeScreen from "./components/WelcomeScreen";
import ConnectedHeader from "./components/ConnectedHeader";
import AgentVisualiser from "./components/AgentVisualiser";
import { FixedTypingIndicator } from "./components/FixedTypingIndicator";
import ToolMagic from "./components/tools/ToolMagic";
import ChatBox from "./components/ChatBox";

export function App() {
  const transportState = useRTVIClientTransportState();
  const client = useRTVIClient();
  const [started, setStarted] = useState(false);

  const isConnected = transportState === 'ready';
  const connecting = ['initializing', 'authenticating', 'connecting', 'connected'].includes(transportState);

  // Handle errors 
  useRTVIClientEvent(
    RTVIEvent.Error,
    useCallback(
      () => {
        console.log('Error occurred');
      },
      []
    )
  );

  useEffect(() => {
    if (isConnected) {
      setStarted(true);
    }
  }, [isConnected])

  const micClick = async () => {
    if (!client) {
      console.error('RTVI client is not initialized');
      return;
    }

    try {
      if (isConnected) {
        await client.disconnect();
      } else {
        setStarted(false);
        await client.connect();
      }
    } catch (error) {
      console.error('Connection error:', error);
    }
  };

  return (
    <div className="bg-gray-100 w-full h-full fixed">
      <NavBar />
      <AgentActions />
      <div className="px-2 md:px-4 max-w-screen-xl mx-auto py-4 h-full w-full flex flex-col">

        <AnimatePresence>
          {!isConnected && !started && (
            <motion.div exit={{ y: -10, opacity: 0 }} className={cn("bg-gray-50 antialiased rounded-sm h-fit overflow-auto py-10 px-0 shadow-md w-full flex flex-col justify-center align-middle", isConnected || started && 'justify-between')} >
              <WelcomeScreen micClick={micClick} connecting={connecting} transportState={transportState} />
            </motion.div>
          )}
        </AnimatePresence>

        {!(!isConnected && !started) && (
          <motion.div initial={{ opacity: 0, y: 10 }} transition={{ delay: 0.5 }}
            animate={{ opacity: 1, y: 0 }} className="flex flex-col w-full rounded-md h-full flex-1">

            <ConnectedHeader connected={isConnected} onBtnClick={micClick} />

            <div className="flex flex-row h-full py-10 overflow-hidden px-2">
              <div className="flex flex-col align-middle justify-start w-full">
                <AgentVisualiser />
                <div className="flex flex-row align-middle justify-center pt-12">
                  <FixedTypingIndicator />
                </div>
                <div className="flex bg-white/95 flex-row rounded-md shadow-[0_0_6px_2px_rgba(0,_0,_0,_0.1)] align-middle justify-center mt-6 mb-10 flex-1 overflow-hidden">
                  <ChatBox />
                </div>
              </div>
            </div>

          </motion.div>
        )}
        <RTVIClientAudio />
      </div>
    </div >
  );
}

export default App;
