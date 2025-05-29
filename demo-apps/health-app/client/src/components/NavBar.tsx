import { MdHealthAndSafety } from "react-icons/md";
import awsLogo from "../assets/aws-logo.svg";

export default function NavBar() {
  return (
    <div className="w-full bg-[#161D26] min-h-14 shadow-md text-white">
      <div className="max-w-screen-xl mx-auto py-2 antialiased px-2 md:px-4 flex flex-row items-center">
        <div className="mr-3 flex items-center">
          <img src={awsLogo} alt="AWS Logo" width="50" height="50" />
        </div>
        <div className="w-2"></div>
        <div className="flex flex-col">
          <p className="font-bold text-md">AI Health Assistant</p>
          <p className="text-sm font-light">Powered by Amazon Nova Sonic</p>
        </div>
      </div>
    </div>
  )
}
