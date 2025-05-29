import BookingSummaryWidget from "./BookingSummaryWidget";
import DoctorAppointments, { shouldAddDoctorsAppointment } from "./DoctorAppointmentsWidget";

// eslint-disable-next-line @typescript-eslint/no-explicit-any
export const availableTools: Record<string, (data: any) => boolean> = {
  'get_non_clashing_slots': shouldAddDoctorsAppointment,
  'book_appointment': () => true
};

type ToolDisplayProps = {
  type: string,
  timestamp: Date,
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  data: any
};

export default function ToolDisplay(props: ToolDisplayProps) {
  if (props.type === 'get_non_clashing_slots') {
    return <DoctorAppointments data={props.data} />
  } else if (props.type === 'book_appointment') {
    return <BookingSummaryWidget data={props.data} />
  } else return null;
}