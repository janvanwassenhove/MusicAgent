import axios from 'axios'

const api = axios.create({
    baseURL: process.env.VUE_APP_API_URL || 'http://localhost:5000'
})

export default {
    getAgentTypes() {
        return api.get('/agent_types')
    },
    initializeAgent(agentType) {
        return api.post('/init', { agent_type: agentType })
    },
    // Add other API methods
}
