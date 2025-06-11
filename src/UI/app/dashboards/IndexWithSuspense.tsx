"use client";

import React, { Suspense } from "react";
import DocumentDashboardPage from "./index";

const IndexWithSuspense = () => (
  <Suspense fallback={<div>Loading chat...</div>}>
    <DocumentDashboardPage />
  </Suspense>
);

export default IndexWithSuspense;


