<template>
  <div>
    <div class="text-center py-2 mb-2" style="background-color: #1A4731;">
      <img src="@/assets/images/musicagent.png" alt="MusicAgent" style="max-width: 100%; height: 200px;">
    </div>
    <div class="container main_container bg-dark text-white">
      <nav class="navbar navbar-expand-lg navbar-light bg-dark text-white">
        <div class="container-fluid">
          <a class="navbar-brand" href="/">MusicAgent</a>
          <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav" aria-controls="navbarNav" aria-expanded="false" aria-label="Toggle navigation">
            <span class="navbar-toggler-icon"></span>
          </button>
          <div class="collapse navbar-collapse" id="navbarNav">
            <ul class="navbar-nav">
              <li class="nav-item">
                <router-link class="nav-link" to="/home">New Song</router-link>
              </li>
              <li class="nav-item">
                <router-link class="nav-link" to="/samples">Samples</router-link>
              </li>
              <li class="nav-item">
                <router-link class="nav-link" to="/songs-library">Song Library</router-link>
              </li>
              <li class="nav-item">
                <router-link class="nav-link" to="/settings">Settings</router-link>
              </li>
            </ul>
          </div>
        </div>
      </nav>

      <div class="slot-container bg-white text-dark">
        <slot></slot>
      </div>
    </div>

    <footer class="container footer_container bg-dark text-white text-center py-3 mb-4">
      <div>
        <p class="mb-0">&copy; 2024 MusicAgent from mITyJohn. All rights reserved.</p>
        <p class="mb-0">Follow mITy.John on
          <a href="https://www.instagram.com/mity.john/" class="text-white"><i class="fab fa-instagram"></i></a>&nbsp;
          <a href="https://www.linkedin.com/in/jan-van-wassenhove-9b49893/" class="text-white"><i class="fab fa-linkedin"></i></a>&nbsp;
          <a href="https://mityjohn.com/" class="text-white"><i class="fab fa-wordpress"></i></a>&nbsp;
          <a href="https://x.com/mity_john" class="text-white"><i class="fab fa-twitter"></i></a>&nbsp;
        </p>
      </div>
    </footer>
  </div>
</template>

<script>
export default {
  name: 'MainLayout'
};
</script>

<style scoped>
.main_container {
  width: 100% !important;
  padding: 5px;
}

.slot-container {
  padding: 20px;
  border-radius: 5px;
}

.footer_container {
  width: 100%;
}
</style>