<template>
  <MainLayout>
    <h1>Welcome to MusicAgent</h1>
    <p>Welome, and get ready to start creating your own songs!<br>
      <br>Click on the "Create New" link in the navigation bar to start creating your own song.
      <br>Click on the "Samples" link in the navigation bar to see some sample songs or launche the metadata listing (if you aded new samples).
      <br>Click on the "Songs Library" link in the navigation bar to see the songs library.
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
</style>