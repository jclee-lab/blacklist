import { redirect } from 'next/navigation';

// Monitoring page has been merged into Dashboard
// Redirect to dashboard for backward compatibility
export default function MonitoringPage() {
  redirect('/');
}
