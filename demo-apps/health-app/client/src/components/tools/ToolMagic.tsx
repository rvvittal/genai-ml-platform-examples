/* eslint-disable @typescript-eslint/no-explicit-any */
import { useCallback, useEffect, useState } from "react";
import { useRTVIClientEvent, useRTVIClientTransportState } from "@pipecat-ai/client-react";
import { LLMFunctionCallData, RTVIEvent } from "@pipecat-ai/client-js";
import ToolDisplay, { availableTools } from "./ToolDisplay";
import { AnimatePresence, motion } from "motion/react";

type ToolEvent = {
  toolId: string,
  invocationId: string,
  args: any
  loading: boolean,
  result: any,
  timestamp: Date,
}

export default function ToolMagic() {
  const transportState = useRTVIClientTransportState();
  const [toolInfo, setToolInfo] = useState<ToolEvent | undefined>();

  useEffect(() => {
    if (transportState === 'initializing') {
      setToolInfo(undefined)
    }
  }, [transportState]);

  const addToolData = useCallback((toolId: string, invocationId: string, args: any, loading: boolean, result: any,) => {
    setToolInfo(
      {
        toolId: toolId,
        invocationId: invocationId,
        args: args,
        loading: loading,
        result: result,
        timestamp: new Date()
      }
    );
  }, []);

  const clearToolData = useCallback(() => {
    setToolInfo(undefined)
  }, [])

  useRTVIClientEvent(
    RTVIEvent.LLMFunctionCall,
    useCallback(
      (data: LLMFunctionCallData) => {
        console.log('LLMFunctionCall:', data);
        const isSuccessful = (data.result as (undefined | { success: boolean }))?.success === true;
        if (isSuccessful) {
          if (Object.keys(availableTools).includes(data.function_name)) {
            const additionCheck = availableTools[data.function_name];
            if (additionCheck(data.result)) {
              addToolData(data.function_name, data.tool_call_id, data.args, isSuccessful, data.result);
            }
          } else {
            addToolData(data.function_name, data.tool_call_id, data.args, isSuccessful, data.result);
          }
        } else {
          clearToolData();
        }
      },
      [addToolData, clearToolData]
    )
  );

  return (
    <div>
      <AnimatePresence>
        {toolInfo && (
          <motion.div exit={{ y: -10, opacity: 0 }} initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}>
            <ToolDisplay type={toolInfo.toolId} timestamp={toolInfo.timestamp} data={toolInfo.result} />
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}