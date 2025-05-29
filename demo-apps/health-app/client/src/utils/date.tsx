export const formatDateBooking = (dateString: string) => {
  const dateObj = new Date(dateString);
  const day = dateObj.getDate();
  const month = dateObj.toLocaleDateString('en-US', { month: 'long', year: 'numeric' });
  const dayOfWeek = dateObj.toLocaleDateString('en-US', { weekday: 'long' });

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

  return <>{dayOfWeek}, {day}<sup>{getOrdinalSuffix(day)}</sup> {month}</>;
}