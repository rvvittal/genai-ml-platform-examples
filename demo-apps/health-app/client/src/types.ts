/* eslint-disable @typescript-eslint/no-explicit-any */
type Message = {
  text: string;
};

export type ToolEvent = {
  toolId: string;
  invocationId: string;
  payload: any;
};

export type Event = (
  | {
      type: "message";
      data: Message;
    }
  | {
      type: "tool";
      data: ToolEvent;
    }
) & {
  id: string;
  sender: "user" | "assistant";
  timestamp: Date;
};
