import { getDoctorAvatar } from "../../utils/doctorAvatars";
import { IoIosCheckmarkCircleOutline } from "react-icons/io";
import { IoCalendarOutline } from "react-icons/io5";
import { IoMdTime } from "react-icons/io";
import { MdOutlineDateRange } from "react-icons/md";
import { IoLocationOutline } from "react-icons/io5";
import { LiaNotesMedicalSolid } from "react-icons/lia";
import { IoInformationCircleOutline } from "react-icons/io5";
import { TiInfoOutline } from "react-icons/ti";
import DoctorDisplay from "./DoctorDisplay";
import { cn } from "../../utils/tailwind";
import { formatDateBooking } from "../../utils/date";
import { capitalize } from "../../utils/strings";

export type BookedSummaryPayload = {
  appointment: {
    "slot_id": string
    "date": string
    "time": string
    "doctor": string
    "user_id": string
    "symptoms_summary": {
      symptoms: { symptom: string, duration: string, intensity: string }[]
      additional_notes: string
    } | undefined,
    "booking_time": string
  }
}

type BookingSummaryWidgetProps = {
  data: BookedSummaryPayload
}

export default function BookingSummaryWidget(props: BookingSummaryWidgetProps) {

  const doctorName = props.data.appointment.doctor;
  const doctorAvatar = doctorName ? getDoctorAvatar(doctorName) : null;

  return (
    <div className={"w-1/2 min-w-[600px] shadow-sm rounded-md"}>
      <div className=" w-full rounded-t-md flex flex-row flex-start align-middle bg-green-600 px-3 py-3 gap-2">
        <div className="self-center">
          <IoIosCheckmarkCircleOutline className="text-4xl text-white" />
        </div>
        <div className="flex-1">
          <h6 className="font-semibold text-xl text-white">Appointment confirmed</h6>
          <p className="text-sm text-white">Your appointment had been confirmed and added to your calendar.</p>
        </div>
      </div>

      <div className="flex flex-col w-full gap-2 shadow-md bg-white px-2 py-3 flex-1 rounded-b-md">

        <div className=" bg-white flex flex-col gap-3 w-full px-3 pb-2">
          <div className="flex flex-row gap-2 align-middle justify-start">
            <h6 className="text-lg font-medium text-gray-900">Appointment Details</h6>
          </div>
          <div className="flex flex-row justify-between gap-3">
            <div className="flex-1">
              <DoctorDisplay doctorName={doctorName} doctorAvatar={doctorAvatar} />
            </div>

            <div className="flex-1 gap-2 flex flex-col">
              <div className="flex flex-row gap-2 align-middle justify-start">
                <MdOutlineDateRange className="text-xl self-center text-gray-500" />
                <div className="text-sm">{formatDateBooking(props.data.appointment.date)}</div>
              </div>
              <div className="flex flex-row gap-2 align-middle justify-start">
                <IoMdTime className="text-xl self-center text-gray-500" />
                <div className="text-sm">{props.data.appointment.time.toLowerCase()}</div>
              </div>
              <div className="flex flex-row gap-2 align-middle justify-start">
                <IoLocationOutline className="text-xl self-center text-gray-500" />
                <div className="text-sm">Amazon Medical Center</div>
              </div>
            </div>
          </div>
        </div>

        <div className=" bg-white flex flex-col gap-3 w-full px-3 py-3 border-t">
          <div className="flex flex-row gap-2 align-middle justify-start">
            <h6 className="text-lg font-medium text-gray-900">Symptom Summary</h6>
          </div>
          <div className="flex flex-col justify-between gap-3 px-2">

            {
              props.data.appointment.symptoms_summary && props.data.appointment.symptoms_summary.symptoms.map(symptom => (
                <div>
                  <div className="flex flex-row gap-2 align-top justify-start">
                    <TiInfoOutline className={cn("text-xl text-gray-600", { 'text-yellow-600': symptom.intensity === 'mild', 'text-red-600': symptom.intensity === 'high' })} />
                    <div className="flex flex-col flex-1">
                      <div className="font-semibold">{capitalize(symptom.symptom)}</div>
                      <p className="text-sm"><span className="font-medium">Duration:</span> {symptom.duration} | <span className="font-medium">Intensity:</span> {symptom.intensity}</p>
                    </div>
                  </div>

                </div>
              ))
            }
          </div>
        </div>

        <div className=" bg-white flex flex-col gap-2 w-full px-3 py-3 border-t">
          <div className="flex flex-row gap-2 align-middle justify-start">
            <h6 className="text-lg font-medium text-gray-900">Additional notes</h6>
          </div>
          <div className="px-2">
            {props.data.appointment.symptoms_summary?.additional_notes || '(none)'}
          </div>
        </div>

        <div className="flex flex-row gap-1 align-middle justify-start text-gray-500 px-3 py-1">
          <IoInformationCircleOutline className="text-sm self-center text-gray-500" />
          <p className="text-xs">A confirmation email had been sent to your inbox with additional details.</p>
        </div>

      </div>

    </div>
  )
}
