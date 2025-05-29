import { cn } from "../utils/tailwind";

type ChatMessageProps = {
  message: string,
  sender: 'user' | 'assistant'
};

export default function ChatMessage(props: ChatMessageProps) {
  return (
    <div className={cn("bg-slate-200 w-fit rounded-md shadow-sm px-3 py-4 subpixel-antialiased", props.sender === 'assistant' && 'bg-gray-200')}>
      {props.message}
    </div>
  )
}