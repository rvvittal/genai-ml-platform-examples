import Spinner from "@cloudscape-design/components/spinner";
import { motion } from "motion/react";
import { MdHealthAndSafety } from "react-icons/md";
import { cn } from "../utils/tailwind";

type WelcomeScreenProps = {
  connecting: boolean;
  transportState: string;
  micClick: () => void
};

export default function WelcomeScreen(props: WelcomeScreenProps) {
  return (
    <div className="text-gray-900 text-center flex flex-col justify-center align-middle">
      <MdHealthAndSafety className="text-aws-orange h-full w-16 mb-3 self-center" />
      <h1 className="text-2xl font-semibold text-gray-950 mb-3">Welcome to AWS AI Health Assistant</h1>
      <p className="mb-12">Ask questions about symptoms, medications, or get health recommendations.</p>
      <div>
        <div className="h-16">
          {props.connecting ? (
            <motion.div initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }} className="flex flex-row align-middle justify-center gap-4">
              <Spinner size="big" /> <p className="self-center">Connecting, please wait</p>
            </motion.div>
          ) : (
            <motion.button
              exit={{ y: -10, opacity: 0 }}
              className={
                cn(
                  "bg-aws-orange hover:bg-aws-orange-light text-white px-4 py-2 font-bold rounded-sm shadow-sm antialiased hover:cursor-pointer hover:shadow-md",
                )}
              onClick={props.micClick}>Talk to assistant</motion.button>
          )}
          {props.transportState === 'error' && <p className="text-red-600 mt-4">Unable to connect at the moment, please try again shortly</p>}
        </div>
      </div>
    </div>
  )
}