import axios from "axios";
import { AllFile } from "../schema/allFile"


export async function downloadFile(audio_id: number , dir :string , file_type:string):Promise<AllFile>{
    let url = `http://localhost:8080/audio/${audio_id}/download?dir=${dir}&file_type=${file_type}`;
    try {
        const response = await axios.get(url);
        
        return response.data;
    } catch (error) {
        if (axios.isAxiosError(error)) {
            throw new Error(`下載失敗: ${error.message}`);
        }
        throw new Error('下載過程中發生未預期的錯誤');
    }
}