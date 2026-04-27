import axios from "axios";

const client = axios.create({
  baseURL: "/api/v1",
  timeout: 300000,
});

export default client;
