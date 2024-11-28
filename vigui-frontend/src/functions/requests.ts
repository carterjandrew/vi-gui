import axios from 'axios'

export const apiClient = axios.create({
	baseURL: `https://${import.meta.env.VITE_API_ADDRESS}`
})


