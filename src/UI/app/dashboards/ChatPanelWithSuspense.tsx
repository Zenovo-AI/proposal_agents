"use client";
import React, { Suspense } from "react";
import ChatPanel from "./chat";

const ChatPanelWithSuspense = (props: any) => (
  <Suspense fallback={<div>Loading chat...</div>}>
    <ChatPanel {...props} />
  </Suspense>
);

export default ChatPanelWithSuspense;
