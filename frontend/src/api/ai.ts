import axios from "axios";
import { Summary } from "../schema/summary"
import { Transcript } from "../schema/transcript";
import { Term } from "../schema/term";
import { Reply } from "../schema/reply";

export async function getSummary(audio_id : number):Promise<Summary>{
    let url = "http://127.0.0.1:8080/ai/summarize/" + audio_id;
    let course;
    try {
        const response = await axios.get(url);
        course = response.data;
    }
    catch(error) {  
        
    }
    return course;
}

export async function getTranscript(audio_id : number):Promise<Transcript>{
    let url = "http://127.0.0.1:8080/ai/transcript/" + audio_id;
    let transcript;
    try {
        const response = await axios.get(url);
        transcript = response.data;
    }
    catch(error) {  
        
    }
    return transcript;
}

export async function getTerm(audio_id : number):Promise<Term>{
    let url = "http://127.0.0.1:8080/ai/term/" + audio_id;
    let term;
    try {
        const response = await axios.get(url);
        term = response.data;
    }
    catch(error) {  
        
    }
    return term;
}

export async function doInference(audio_id : number):Promise<void>{
    let url = "http://127.0.0.1:8080/ai/inference/" + audio_id;
    try {
        const response = await axios.get(url);
    }
    catch(error) {  
        
    }
}

export async function getReply(query :string):Promise<Reply>{
    let url = "http://127.0.0.1:8080/ai/chatbot?query=" + query;
    let reply;
    try {
        const response = await axios.get(url);
        reply = response.data;
    }
    catch(error) {  
        
    }
    return reply;
}

