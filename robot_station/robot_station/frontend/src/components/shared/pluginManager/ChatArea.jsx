import { useEffect, useState } from "react";

export function ChatArea({ msgList }) {
    console.log("msglist:", msgList);

    const chatBoxes = msgList.map((element) => {
        return (
            <li
                key={element.id}
                className={
                    element.msgType === "sent" ? "msg-sent" : "msg-received"
                }
            >
                {element.text}
            </li>
        );
    });

    return (
        <div className="chat-area">
            <p>Chat</p>
            <ul>{chatBoxes}</ul>
        </div>
    );
}

export function useChatHistory(initMsgList) {
    const [msgList, setMsgList] = useState(initMsgList);
    const [idCounter, setIdCounter] = useState(0);

    const updateSentMsg = (msgSent) => {
        setMsgList((s) => [
            ...s,
            { id: idCounter, msgType: "sent", text: msgSent },
        ]);
        setIdCounter((s) => s + 1);
    };

    const updateReceivedMsg = (msgReceived) => {
        setMsgList((s) => [
            ...s,
            { id: idCounter, msgType: "received", text: msgReceived },
        ]);
        setIdCounter((s) => s + 1);
    };

    return [msgList, updateReceivedMsg, updateSentMsg];
}
