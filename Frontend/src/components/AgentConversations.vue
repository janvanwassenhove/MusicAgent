<template>
  <div id="agentConversations" class="py-4 collapse show">
    <h3>Agent Conversations</h3>
    <div id="chats" class="mt-4 mb-4 py-4"></div>
  </div>
</template>

<script>
import { mapState } from 'vuex'

export default {
  name: 'AgentConversations',
  computed: {
    ...mapState({

    })
  },
  methods: {
    handleAgentConversations(e) {
      if (!e || !e.data) {
        console.info('Event data is undefined');
        return;
      }

      const parameterRegexQuestioner = /\[Questioner\]\(([A-Za-z0-9_\s]+)\):\[\[(.*?)\]\]/g;
      const matchesQuestioner = [...e.data.matchAll(parameterRegexQuestioner)];
      const chatsDiv = document.getElementById('chats');
      matchesQuestioner.forEach(match => {
        const firstParam = match[1];
        const secondParam = match[2];

        // Create the container for the chat message
        const chatMessage = document.createElement('div');
        chatMessage.className = 'chat-message d-flex align-items-start mb-3';

        // Create the image element
        const img = document.createElement('img');
        img.src = require(`@/assets/images/assistants/${firstParam.replace(/ /g, '_')}.webp`);
        img.onerror = () => {
          img.src = require('@/assets/images/assistants/Unknown.webp');
        };
        img.alt = firstParam;
        img.className = 'chat-image me-3';

        const textContainer = document.createElement('div');
        textContainer.className = 'chat-text p-3 rounded';

        const textContent = document.createElement('div');
        const maxLength = 1000; // Adjust the length as needed
        textContent.innerHTML = `<strong>${firstParam}:</strong> `;
        for (let i = 0; i < secondParam.length; i += maxLength) {
          textContent.innerHTML += `<em>${secondParam.substring(i, i + maxLength)}</em>`;
        }

        textContainer.appendChild(textContent);
        chatMessage.appendChild(img);
        chatMessage.appendChild(textContainer);
        chatsDiv.appendChild(chatMessage);
      });

      const parameterRegexAssistant = /\[Assistant\]\(([A-Za-z0-9_\s]+)\):\[\[(.*?)\]\]/g;
      const matchesAssistant = [...e.data.matchAll(parameterRegexAssistant)];
      matchesAssistant.forEach(match => {
        const firstParam = match[1];
        const secondParam = match[2];

        // Create the container for the chat message
        const chatMessage = document.createElement('div');
        chatMessage.className = 'chat-message d-flex align-items-start justify-content-end mb-3';

        // Create the text container
        const textContainer = document.createElement('div');
        textContainer.className = 'chat-text p-3 rounded me-3';

        // Create the text content
        const textContent = document.createElement('div');
        const maxLength = 1000; // Adjust the length as needed

        if (secondParam.startsWith("Cover image generated https://")) {
          const url = secondParam.split(" ")[3];
          textContent.innerHTML = `<strong>${firstParam}:</strong> <em>Cover image generated:</em> <img src="${url}" alt="Cover Image" style="max-width: 100%; height: auto;">`;
        } else {
          textContent.innerHTML = `<strong>${firstParam}:</strong> `;
          for (let i = 0; i < secondParam.length; i += maxLength) {
            textContent.innerHTML += `<em>${secondParam.substring(i, i + maxLength)}</em>`;
          }
        }

        const img = document.createElement('img');
        img.src = require(`@/assets/images/assistants/${firstParam.replace(/ /g, '_')}.webp`);
        img.onerror = () => {
          img.src = require('@/assets/images/assistants/Unknown.webp');
        };
        img.alt = firstParam;
        img.className = 'chat-image';

        // Append elements
        textContainer.appendChild(textContent);
        chatMessage.appendChild(textContainer);
        chatMessage.appendChild(img);
        chatsDiv.appendChild(chatMessage);
      });

    }
  },
  mounted() {
    this.handleAgentConversations()
  }
}
</script>
