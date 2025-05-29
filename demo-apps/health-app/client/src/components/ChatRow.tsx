import { MdHealthAndSafety } from "react-icons/md";
import { cn } from "../utils/tailwind";
import Avatar from "@cloudscape-design/chat-components/avatar";

type ChatRowProps = {
  sender: 'user' | 'assistant'
  hideIcon: boolean;
  timestamp: Date
  children: React.ReactNode
};

export default function ChatRow(props: ChatRowProps) {

  return (
    <div className={cn("w-full px-4 h-auto flex flex-row gap-4", props.sender === 'assistant' ? '' : 'flex-row-reverse')}>
      {/* Icon */}
      <div className={cn({ 'invisible': props.hideIcon })}>
        {
          props.sender === 'user' ? (
            <div className="max-w-12 flex justify-center align-middle">
              <Avatar
                ariaLabel="Avatar of user"
                color="default"
                tooltipText="User"
                width={40}
              />
            </div>
          ) : (
            <div className="max-w-12 flex justify-center align-middle ">
              <MdHealthAndSafety className="text-aws-orange h-full w-16 mb-3 self-center" />
            </div>
          )
        }
      </div>

      {/* Message Box */}
      <div className={cn("w-full flex-1", props.sender === 'user' && 'justify-items-end')}>
        {props.children}
        <div className={'text-gray-400 py-1 text-sm'}>{props.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</div>
      </div>
    </div>
  )
}
