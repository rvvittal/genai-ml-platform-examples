import { cn } from "../utils/tailwind";

type ConnectedHeaderProps = {
  connected: boolean
  onBtnClick: () => void
};

export default function ConnectedHeader(props: ConnectedHeaderProps) {
  return (
    <div className="w-full flex flex-row justify-between px-4 py-4 bg-aws-dark-blue-light text-white rounded-md">
      <div className="w-full flex flex-row gap-4 text-xl font-medium justify-start align-middle h-full text-center">
        <div className="self-center">
          Connected to AI Health Assistant
        </div>
        <div className="bg-green-500 self-center rounded-full shadow-sm shadow-green-300 w-3 h-3">&nbsp;</div>
      </div>
      <div>
        <button onClick={props.onBtnClick} className={
          cn(
            "max-w-12 font-semibold border-r-2 max-w-auto rounded-md border-0 text-white py-1 px-2 flex justify-center align-middle shadow-sm antialiased hover:cursor-pointer hover:shadow-md",
            props.connected ? 'bg-red-600 hover:bg-red-500' : 'bg-aws-orange hover:bg-aws-orange-light'
          )}>
          {props.connected ? <>End&nbsp;call</> : <>Restart</>}
        </button>
      </div>
    </div>
  )
}