import drSmith from '../assets/avatars/Dr. Smith.png';
import drWilliams from '../assets/avatars/Dr. Williams.png';
import drJohnson from '../assets/avatars/Dr. Johnson.png';
import drDavis from '../assets/avatars/Dr. Davis.png';

// Map of doctor names to their avatar images
const doctorAvatars: Record<string, string> = {
  'Dr. Smith': drSmith,
  'Dr. Williams': drWilliams,
  'Dr. Johnson': drJohnson,
  'Dr. Davis': drDavis,
};

// Default avatar to use when no specific avatar is found
const defaultAvatar = drSmith;

/**
 * Get the avatar image for a specific doctor
 * @param doctorName Full name of the doctor
 * @returns URL to the doctor's avatar image
 */
export const getDoctorAvatar = (doctorName: string): string => {
  // Check for exact matches
  if (doctorAvatars[doctorName]) {
    return doctorAvatars[doctorName];
  }
  
  // Check for partial matches
  for (const [name, avatar] of Object.entries(doctorAvatars)) {
    if (doctorName.includes(name)) {
      return avatar;
    }
  }
  
  // Return default avatar if no match found
  return defaultAvatar;
};

export default doctorAvatars; 