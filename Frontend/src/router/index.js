import { createRouter, createWebHistory } from 'vue-router';
import Welcome from '../views/Welcome.vue';
import Song from '../views/Song.vue';
import SampleList from '../views/SampleList.vue';
import SongsLibrary from '../views/SongsLibrary.vue';

const routes = [
  {
    path: '/',
    name: 'Welcome',
    component: Welcome
  },
  {
    path: '/home',
    name: 'Song',
    component: Song
  },
  {
    path: '/samples',
    name: 'SampleList',
    component: SampleList
  },
  {
    path: '/songs-library',
    name: 'SongsLibrary',
    component: SongsLibrary
  }
];

const router = createRouter({
  history: createWebHistory(process.env.BASE_URL),
  routes
});

export default router;
