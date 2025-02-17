import axios from 'axios';

export async function uploadAudio(audio_id: number, dir: string, file_type: string, audioBlob: Blob): Promise<void> {
    const url = `http://localhost:8080/audio/${audio_id}/upload`;
    
    const formData = new FormData();
    formData.append('dir', dir);
    formData.append('file_type', file_type);
    formData.append('file', audioBlob, `${audio_id}.${file_type}`);

    try {
        await axios.post(url, formData, {
            headers: {
                'Content-Type': 'multipart/form-data',
            },
        });
    } catch (error) {
        if (axios.isAxiosError(error)) {
            throw new Error(`上傳失敗: ${error.message}`);
        }
        throw new Error('上傳過程中發生未預期的錯誤');
    }
}