/**
 * this is a client component
 * and it is used to display the login page
 * and handle the login process
 * and it is used to display the login page
 */ 


import { Suspense } from "react";
import ProfileClient from "./ProfileClient";

export default function ProfilePage() {
  return (
    <Suspense fallback={<p>Loading user info...</p>}>
      <ProfileClient />
    </Suspense>
  );
}