import axios from "axios";
import { Audio } from "../schema/audio"


export async function postAudioWithFile(audio: Audio, file: File): Promise<Audio> {
    let url = "http://localhost:8080/audio";
    const formData = new FormData();
    
    formData.append("title", audio.title || "");
    formData.append("info", audio.info || "");
    formData.append("audio_file", file);  
  
    try {
      const response = await axios.post(url, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      return response.data;
    } catch (error) {
      throw error;
    }
  }

export async function postAudio(audio:Audio): Promise<Audio>{
    let url = "http://localhost:8080/audio/normal" ;
    let created_audio;
    try {
        const response = await axios.post(url,audio);
        created_audio = response.data;
    }
    catch(error) {  
        
    }
    return created_audio ; 
}


export async function getAudioList(): Promise<Array<Audio>>{
    let url = "http://localhost:8080/audio";
    
    try {
        const response = await axios.get(url,);
        return response.data;
    }
    catch {  
        
        return [];
    }
}

export async function getAudio(id:number): Promise<Audio>{
    let url = "http://localhost:8080/audio/" + id;
    let audio;
    try {
        const response = await axios.get(url,);
        audio = response.data;
    }
    catch {  
        
        //return ;
    }
    return audio ; 
}

export async function updateAudio(audio:Audio){
  let url = "http://localhost:8080/audio/"+audio.id;
  try {
      const response = await axios.put(url,audio);
  }
  catch(error) {  
      
  }
}


interface SearchParams {
  start_date?: string;
  end_date?: string;
  title?: string;
  info?: string;
  term?: string;
  transcript? :string;
}


export async function searchAudio(params?: SearchParams): Promise<Array<Audio>>{
  let url = "http://localhost:8080/audio/db/search";
  try {
    const queryParams = new URLSearchParams();
    
    if (params) {
      if (params.start_date) queryParams.append('start_date', params.start_date);
      if (params.end_date) queryParams.append('end_date', params.end_date);
      if (params.title) queryParams.append('title', params.title);
      if (params.info) queryParams.append('info', params.info);
      if (params.term) queryParams.append('term', params.term);
      if (params.transcript) queryParams.append('transcript', params.transcript);
    }

    // 如果有查詢參數，將其加到 URL 後面
    const finalUrl = queryParams.toString() 
      ? `${url}?${queryParams.toString()}` 
      : url;

    const response = await axios.get(finalUrl);
    return response.data;
  }
  catch(error) {  
    return [];
  }

}
