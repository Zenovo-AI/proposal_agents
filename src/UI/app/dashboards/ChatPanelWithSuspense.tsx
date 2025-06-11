"use client";
import React, { Suspense } from "react";
import ChatPanel from "./chat";
import type { ChatPanelProps } from "./chat";

const ChatPanelWithSuspense = (props: ChatPanelProps) => (
  <Suspense fallback={<div>Loading chat...</div>}>
    <ChatPanel {...props} />
  </Suspense>
);

export default ChatPanelWithSuspense;
