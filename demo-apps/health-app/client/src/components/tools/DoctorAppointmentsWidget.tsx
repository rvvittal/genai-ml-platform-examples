
import { MdOutlineDateRange } from "react-icons/md";
import { groupBy } from "../../utils/collections";
import { getDoctorAvatar } from "../../utils/doctorAvatars";
import DoctorDisplay from "./DoctorDisplay";

export type GetAvailableSlotsPayload = {
  non_clashing_slots: DoctorAppointments
}

export type DoctorAppointments = {
  id: string;
  date: string;
  time: string;
  doctor: string;
}[]

type DoctorAppointmentsWidgetProps = {
  data: GetAvailableSlotsPayload
}

export const shouldAddDoctorsAppointment = (data: any) => {
  if (data && "non_clashing_slots" in data && data.non_clashing_slots.length > 0) {
    return true;
  }
  return false;
}

export default function DoctorAppointmentsWidget(props: DoctorAppointmentsWidgetProps) {

  const appointments = props.data.non_clashing_slots;
  appointments.sort((a, b) => {
    const dateA = new Date(`${a.date} ${a.time}`);
    const dateB = new Date(`${b.date} ${b.time}`);
    return dateA.valueOf() - dateB.valueOf();
  });

  const doctorName = props.data.non_clashing_slots[0]?.doctor;
  const groupedAppointments = groupBy(appointments, "date");

  // Get the doctor's avatar image
  const doctorAvatar = doctorName ? getDoctorAvatar(doctorName) : null;

  const formatDate = (dateString: string) => {
    const dateObj = new Date(dateString);
    const weekday = dateObj.toLocaleDateString('en-US', { weekday: 'long' })
    const day = dateObj.getDate();
    const month = dateObj.toLocaleDateString('en-US', { month: 'short' });

    function getOrdinalSuffix(day: number) {
      if (day >= 11 && day <= 13) {
        return 'th';
      }
      switch (day % 10) {
        case 1: return 'st';
        case 2: return 'nd';
        case 3: return 'rd';
        default: return 'th';
      }
    }

    return <>{weekday}, {day}<sup>{getOrdinalSuffix(day)}</sup> {month}</>;
  }

  return (
    <div className={"w-1/3 min-w-96 rounded-md shadow-md"}>

      {/* Message Box */}

      <div className="bg-aws-dark-blue text-white rounded-t-md">
        <DoctorDisplay doctorName={doctorName} doctorAvatar={doctorAvatar} theme="dark" />
      </div>

      <div className="flex flex-col w-full gap-3 bg-white px-4 py-3 flex-1 rounded-b-md">
        <h6 className="text-lg font-medium text-gray-900">Available Appointments</h6>
        {
          Object.keys(groupedAppointments).map(dateKey => {
            return (
              <div key={dateKey} className="mb-2">
                <div className="flex flex-row gap-2 align-middle justify-start mb-2">
                  <MdOutlineDateRange className="text-xl self-center" />
                  <p className="text-left text-md antialiased text-aws-dark-blue ">{formatDate(dateKey)}</p>
                </div>
                <div className="flex flex-row flex-wrap gap-2">
                  {groupedAppointments[dateKey].map(time => {
                    return (
                      <div key={time.id} className=" bg-gray-100 rounded-md border text-sm flex flex-row gap-3 w-fit px-3 py-2 ">
                        <p className="text-gray-600 font-medium text-md">{time.time}</p>
                      </div>
                    )
                  })}
                </div>
              </div>
            );
          })
        }
      </div>
    </div>
  )
}
