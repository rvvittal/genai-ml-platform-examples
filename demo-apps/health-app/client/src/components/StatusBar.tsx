import { FaMicrophone } from "react-icons/fa";

type StatusBarProps = {
  onMicClick: () => void,
  onDisplayProcessingClick: () => void,
  status: 'LISTENING' | 'CONNECTING' | 'PROCESSING' | 'SPEAKING'
};

const statusMessages = {
  'LISTENING': 'Listening ...',
  'CONNECTING': 'Connecting',
  'PROCESSING': 'Processing',
  'SPEAKING': 'Speaking',
}

export function StatusBar(props: StatusBarProps) {
  return (
    <div className="pt-4 px-4 flex flex-row align-middle gap-4">
      <div className="flex flex-row gap-2 self-center">
        <button onClick={props.onMicClick} className="max-w-12 border-r-2 rounded-full bg-aws-orange p-2 flex justify-center align-middle shadow-sm antialiased hover:bg-aws-orange-light hover:cursor-pointer hover:shadow-md">
          <FaMicrophone size={'1.4em'} className="p-0 m-0 text-slate-100" />
        </button>
      </div>
      <div className="self-center justify-center">
        {statusMessages[props.status]}
      </div>
    </div>
  )
}