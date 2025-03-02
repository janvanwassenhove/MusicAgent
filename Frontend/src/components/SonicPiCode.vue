<template>
  <div id="sonicPiCode" class="py-4 collapse show">
    <h3>Sample Sonic Pi Code</h3>
    <div class="mt-4 sonic-pi-code py-4">
      <div>
        <ul class="nav nav-tabs" id="sonicPiCodeTabs" role="tablist"></ul>
        <div class="tab-content" id="sonicPiCodeContent"></div>
      </div>
    </div>
  </div>
</template>

<script>
import { mapState } from 'vuex'
import axios from 'axios'

export default {
  name: 'SonicPiCode',
  computed: {
    ...mapState({
      sonicPiCodeVersions: state => state.sonicPiCodeVersions
    })
  },
  methods: {
    updateSonicPiCodeTabs() {
      const tabsContainer = document.getElementById('sonicPiCodeTabs');
      const contentContainer = document.getElementById('sonicPiCodeContent');

      if (!tabsContainer || !contentContainer) {
        console.debug('Tabs or content container not found in the DOM.');
        return; // Exit the function if elements are not found
      }

      tabsContainer.innerHTML = '';
      contentContainer.innerHTML = '';

      this.sonicPiCodeVersions.forEach((code, index) => {
        const tabId = `sonicPiCodeTab${index}`;
        const contentId = `sonicPiCodeContent${index}`;

        // Create tab
        const tab = document.createElement('button');
        tab.className = 'nav-link';
        tab.id = `${tabId}-tab`;
        tab.setAttribute('data-bs-toggle', 'tab');
        tab.setAttribute('data-bs-target', `#${contentId}`);
        tab.type = 'button';
        tab.role = 'tab';
        tab.ariaControls = contentId;
        tab.ariaSelected = index === 0 ? 'true' : 'false';
        tab.innerText = `Version ${index + 1}`;
        tabsContainer.appendChild(tab);

        const content = document.createElement('div');
        content.className = 'tab-pane fade';
        content.id = contentId;
        content.role = 'tabpanel';
        content.ariaLabelledby = `${tabId}-tab`;
        content.innerHTML = `
          <div class="code-container">
            <button class="copy-icon" title="Copy to clipboard"><i class="fas fa-copy"></i></button>
            <button class="send-icon" title="Send to Sonic Pi"><i class="fas fa-play"></i></button>
            <pre class="sonic-pi-code"><code>${this.parseSonicPiCode(code)}</code></pre>
          </div>`;

        contentContainer.appendChild(content);

        // Set active class for the first tab and content only
        if (index === 0) {
          tab.classList.add('active');
          content.classList.add('show', 'active');
        }

        // Add click event listener to manage active class
        tab.addEventListener('click', () => {
          // Remove active class from all tabs
          const allTabs = document.querySelectorAll('#sonicPiCodeTabs .nav-link');
          allTabs.forEach(t => {
            t.classList.remove('active');
            t.setAttribute('aria-selected', 'false');
          });

          // Add active class to the clicked tab
          tab.classList.add('active');
          tab.setAttribute('aria-selected', 'true');

          // Remove active class from all content
          const allContents = document.querySelectorAll('#sonicPiCodeContent .tab-pane');
          allContents.forEach(c => {
            c.classList.remove('show', 'active');
          });

          // Show the corresponding content
          content.classList.add('show', 'active');
        });

        content.querySelector('.copy-icon').addEventListener('click', () => {
          const codeText = content.querySelector('code').innerText; // Get the code text
          navigator.clipboard.writeText(codeText).then(() => {
            alert('Sonic Pi Code copied to clipboard!'); // Optional: Show a success message
          }).catch(err => {
            console.error('Failed to copy the Sonic Pi code: ', err);
          });
        });
        content.querySelector('.send-icon').addEventListener('click', () => {
          const codeText = content.querySelector('code').innerText; // Get the code text
          this.sendCodeToSonicPi(codeText);
        });

      });

      // Set up the event listener for tab changes
      document.addEventListener('shown.bs.tab', (event) => {
        const activeTab = event.target; // Newly activated tab
        const previousTab = event.relatedTarget; // Previous active tab
        console.log(`Activated tab: ${activeTab.innerText}, Previous tab: ${previousTab ? previousTab.innerText : 'None'}`);
      });
    },
    parseSonicPiCode(code) {
      const keywordRegex = /\b(live_loop|play|sleep)\b/g;
      const numberRegex = /\b\d+(\.\d+)?\b/g;
      const functionRegex = /(:\w+)/g;
      const doendRegex = /\b(do|end)\b/g;

      code = code.replace(keywordRegex, '<span class="keyword">$&</span>');
      code = code.replace(numberRegex, '<span class="number">$&</span>');
      code = code.replace(functionRegex, '<span class="function">$&</span>');
      code = code.replace(doendRegex, '<span class="doend">$&</span>');

      return code;
    },
    sendCodeToSonicPi(code) {
      const songName = this.$store.state.formData.song_name || 'Untitled';
      const agentType = this.$store.state.formData.agent_type || 'mITyJohn';

      axios.post(`${process.env.VUE_APP_API_URL}/api/send_to_sonicpi`, {
        code: code,
        song_name: songName,
        agent_type: agentType
      })
          .then(response => {
            console.info('Code sent to Sonic Pi: ' + response.data.message);
          })
          .catch(error => {
            console.error('Error sending code to Sonic Pi:', error);
            alert('Failed to send the code to Sonic Pi, did you run SonicPi/Setup/recording.rb in Sonic Pi?');
          });
    },
    async fetchSonicPiCode(songname) {
      try {
        const response = await axios.get(`${process.env.VUE_APP_API_URL}/api/get_sonicpi_code/${songname}`);
        console.info('Polling for sonic pi file');
        if (response.data.sonicpi_code) {
          const newCode = response.data.sonicpi_code;
          if (!this.sonicPiCodeVersions.includes(newCode)) {
            console.info('New Version Code Found:', newCode);
            this.sonicPiCodeVersions.push(newCode);
            this.updateSonicPiCodeTabs();
          }
        }
      } catch (error) {
        console.error('Error fetching Sonic Pi code:', error);
      }
    }
  },
  mounted() {
    this.updateSonicPiCodeTabs();
  }
}
</script>

<style scoped>
/* Add any component-specific styles here */
</style>