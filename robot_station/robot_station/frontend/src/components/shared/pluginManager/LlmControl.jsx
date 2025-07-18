import { useEffect, useState } from "react";

import { useRosPub } from "../utils/useRosPub";

import { useRosSub } from "../utils/useRosSub";

import { ChatArea, useChatHistory } from "./ChatArea";

const userQueryTopic = "/user_query";
const llmResponseTopic = "/llm_response";
const stringMessageType = "/std_msgs/msg/String";

export function LlmControl() {
    const publish = useRosPub(userQueryTopic, stringMessageType);
    const subscriber = useRosSub(llmResponseTopic, stringMessageType, 1);

    const [msgList, updateReceivedMsg, updateSentMsg] = useChatHistory([]);

    //const [llmResponse, setLlmResponse] = useState(null);


    const [userQuery, setUserQuery] = useState("");

    useEffect(() => {
        if (subscriber) {
            console.log("LLM response : ", subscriber);
            let llmResponse = String(JSON.parse(subscriber).data);
            updateReceivedMsg(llmResponse);
        }



    }, [subscriber]);

    const handleQuery = () => {
        updateSentMsg(userQuery);
        let queryMsg = String(userQuery).trim();
        if (queryMsg.length !== 0) {
            publish(queryMsg);
        }

        setUserQuery("");



    }

    return (
        <>
            <br />
            <ChatArea msgList={msgList} />
            <textarea className="LlmInput" type="text" value={userQuery} placeholder="Enter your command" spellCheck="true" onChange={(event) => setUserQuery(event.target.value)} onKeyDown={(event) => { event.key === "Enter" && handleQuery() }}>
            </textarea>
            <button className="SubmitButton" onClick={() => handleQuery()}>Submit</button>

        </>

    );
}
