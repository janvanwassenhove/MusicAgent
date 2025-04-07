<template>
  <MainLayout>
    <img src="@/assets/images/road_robots.png" alt="Road Robots" class="responsive-image" />
    <br/><br>
    <h1>Welcome to MusicAgent</h1>

    <p>Welcome, and get ready to start creating your own songs!<br>
      <br>Click on the "New Song" link in the navigation bar to start creating your own song.
      <br>Click on the "Samples" link in the navigation bar to see some sample songs or launch the metadata listing (if you aded new samples).
      <br>Click on the "Songs Library" link in the navigation bar to see the songs library.
      <br>Click on the "Settings" link in the navigation bar to adjust Music Agent settings (Sonic Pi, styling, ...).
    </p>
  </MainLayout>
</template>

<script>
import MainLayout from '@/layouts/MainLayout.vue'

export default {
  name: 'WelcomePage',
  components: {
    MainLayout
  }
}
</script>

<style scoped>
.responsive-image {
  max-width: 100%;
  height: auto;
}
</style>
