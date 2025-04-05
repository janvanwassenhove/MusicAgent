<template>
  <MainLayout>
    <div class="container">
      <h1 class="my-4">Songs Library</h1>
      <div v-if="songs.length === 0">
        <p>No songs available.</p>
      </div>
      <ul v-else class="list-group">
        <li v-for="song in paginatedSongs" :key="song.name" class="list-group-item d-flex justify-content-between align-items-center">
          <div class="d-flex align-items-center" @click="toggleSongDetails(song.name)">
            <img :src="song.thumbnail" alt="Thumbnail" class="thumbnail me-3" v-if="song.thumbnail">
            <span  style="cursor: pointer;">{{ song.name }}</span>
          </div>
          <button class="btn btn-danger btn-sm" @click="deleteSong(song.name)">Delete</button>
        </li>
      </ul>
      <div v-if="songs.length > 5" class="pagination mt-3">
        <button class="btn btn-primary" @click="prevPage" :disabled="currentPage === 1">Previous</button>
        <span class="mx-2 text-dark">Page {{ currentPage }} of {{ totalPages }}</span>
        <span class="mx-2 text-dark">Total Songs: {{ songs.length }}</span>
        <button class="btn btn-primary" @click="nextPage" :disabled="currentPage === totalPages">Next</button>
        </div>
         <hr>
          <div v-if="selectedSong" class="song-details mt-4">
        <div class="row">
          <div class="col-md-6 d-flex flex-column">
            <h2>Song "{{ selectedSong }}"</h2>
            <img :src="albumImage" alt="Album Cover" class="img-fluid" v-if="albumImage">
          </div>
          <div class="col-md-6 d-flex flex-column">
            <h3>Sonic Pi Code</h3>
            <div class="code-container flex-grow-1">
              <button class="copy-icon" title="Copy to clipboard" @click="copyCode"><i class="fas fa-copy"></i></button>
              <button class="send-icon" title="Send to Sonic Pi" @click="sendCodeToSonicPi"><i class="fas fa-play"></i></button>
              <pre class="sonic-pi-code"><code v-html="parsedSonicPiCode"></code></pre>
              <button class="btn btn-secondary mt-2" @click="goToCreativeMode"><i class="fas fa-arrow-right"></i> Open in Creative Mode</button>

            </div>
          </div>
        </div>
      </div>
    </div>
  </MainLayout>
</template>

<script>
import axios from 'axios';
import MainLayout from '@/layouts/MainLayout.vue';

export default {
  name: 'SongsLibrary',
  components: {
    MainLayout
  },
  data() {
    return {
      songs: [],
      selectedSong: null,
      albumImage: null,
      sonicPiCode: null,
      currentPage: 1,
      songsPerPage: 5
    };
  },
  computed: {
    totalPages() {
      return Math.ceil(this.songs.length / this.songsPerPage);
    },
    paginatedSongs() {
      const start = (this.currentPage - 1) * this.songsPerPage;
      const end = start + this.songsPerPage;
      return this.songs.slice(start, end);
    },
    parsedSonicPiCode() {
      return this.sonicPiCode ? this.parseSonicPiCode(this.sonicPiCode) : '';
    }
  },
  methods: {
    async fetchSongs() {
      try {
        const response = await axios.get(`${process.env.VUE_APP_API_URL}/api/songs`);
        const songs = response.data.songs;
        this.songs = await Promise.all(songs.map(async (song) => {
          const thumbnail = await this.fetchThumbnail(song);
          return { name: song, thumbnail };
        }));
      } catch (error) {
        console.error('Error fetching songs:', error);
      }
    },
    async fetchThumbnail(song) {
      try {
        const response = await axios.get(`${process.env.VUE_APP_API_URL}/api/songs/${song}/image`, { responseType: 'blob' });
        return URL.createObjectURL(response.data);
      } catch (error) {
        console.error(`Error fetching thumbnail for song ${song}:`, error);
        return null;
      }
    },
    async deleteSong(song) {
      if (confirm(`Are you sure you want to delete the song "${song}"?`)) {
        try {
          await axios.delete(`${process.env.VUE_APP_API_URL}/api/songs/${song}`);
          this.songs = this.songs.filter(s => s.name !== song);
          if (this.currentPage > this.totalPages) {
            this.currentPage = this.totalPages;
          }
        } catch (error) {
          console.error('Error deleting song:', error);
        }
      }
    },
    async toggleSongDetails(song) {
      if (this.selectedSong === song) {
        this.selectedSong = null;
        this.albumImage = null;
        this.sonicPiCode = null;
      } else {
        this.selectedSong = song;
        await this.fetchSongDetails(song);
      }
    },
    async fetchSongDetails(song) {
      try {
        const imageResponse = await axios.get(`${process.env.VUE_APP_API_URL}/api/songs/${song}/image`, { responseType: 'blob' });
        this.albumImage = URL.createObjectURL(imageResponse.data);

        const codeResponse = await axios.get(`${process.env.VUE_APP_API_URL}/api/get_sonicpi_code/${song}`);
        this.sonicPiCode = codeResponse.data.sonicpi_code;
      } catch (error) {
        console.error('Error fetching song details:', error);
      }
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
    copyCode() {
      const codeText = this.sonicPiCode; // Get the code text
      navigator.clipboard.writeText(codeText).then(() => {
        alert('Sonic Pi Code copied to clipboard!'); // Optional: Show a success message
      }).catch(err => {
        console.error('Failed to copy the Sonic Pi code: ', err);
      });
    },
    sendCodeToSonicPi() {
      const codeText = this.sonicPiCode; // Get the code text
      const songName = this.selectedSong || 'Untitled';
      const agentType = 'mITyJohn'; // Replace with the actual agent type if needed

      axios.post(`${process.env.VUE_APP_API_URL}/api/send_to_sonicpi`, {
        code: codeText,
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
    goToCreativeMode() {
      const songName = this.selectedSong || 'Untitled';
      window.location.href = `/creative-mode?song=${encodeURIComponent(songName)}`;
    },
    prevPage() {
      if (this.currentPage > 1) {
        this.currentPage--;
      }
    },
    nextPage() {
      if (this.currentPage < this.totalPages) {
        this.currentPage++;
      }
    }
  },
  mounted() {
    this.fetchSongs();
  }
};
</script>

<style scoped>
.img-fluid {
    max-height: 600px;
    border-color: #1A4731;
    border: 1px solid #1A4731;
    border-radius: 5px;
}
.thumbnail {
  width: 50px;
  height: 50px;
  object-fit: cover;
}

.sonic-pi-code {
  background-color: #f8f9fa;
  padding: 10px;
  border-radius: 5px;
  white-space: pre-wrap;
  max-height: 600px;
  overflow-y: auto;
}

.keyword {
  color: #d73a49;
  font-weight: bold;
}

.number {
  color: #005cc5;
}

.function {
  color: #6f42c1;
}

.doend {
  color: #d73a49;
  font-weight: bold;
}

.pagination {
  display: flex;
  justify-content: center;
  align-items: center;
}

.pagination button {
  margin: 0 10px;
}
</style>
