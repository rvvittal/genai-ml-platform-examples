
import Avatar from "@cloudscape-design/chat-components/avatar";
import Rating from "@mui/material/Rating";
import { cn } from "../../utils/tailwind";

type DoctorDisplayProps = {
  doctorAvatar?: string | null
  doctorName: string
  theme?: 'dark' | 'light'
};

export default function DoctorDisplay(props: DoctorDisplayProps) {
  return (
    <div className="text-left px-4 py-3 flex-1 flex flex-row gap-4 align-middle justify-start">
      {props.doctorAvatar ? (
        <div className="h-15 w-15 overflow-hidden">
          <img
            src={props.doctorAvatar}
            alt={`${props.doctorName} avatar`}
            className="h-full w-full object-cover"
            style={{ width: '60px', height: '60px', borderRadius: '30%' }}
          />
        </div>
      ) : (
        <Avatar
          ariaLabel="Avatar of user"
          color="default"
          tooltipText="User"
          width={60}
        />
      )}
      <div className="flex-1 pr-5">
        <div className="font-semibold">{props.doctorName}</div>
        <div className={cn("text-sm text-gray-500", { 'text-gray-200': props.theme === 'dark' })}>General Practitioner</div>
        <span className='-ml-[2px]'><Rating readOnly name="half-rating" defaultValue={4.5} precision={0.5} size="small" /></span>
      </div>
    </div>
  )
}