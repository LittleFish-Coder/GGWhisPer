import axios from "axios";

export function setRequestConfig() {
  axios.interceptors.request.use(async (config) => {
    config.baseURL = process.env.REACT_APP_API_END_POINT ?? "";
    return config;
  });
}