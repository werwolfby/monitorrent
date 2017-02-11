<template>
  <div>
    <mt-topics-execute></mt-topics-execute>
    <mt-topics-header></mt-topics-header>
    <mt-topics-list :topics="topics"></mt-topics-list>
  </div>
</template>

<script>
import TopicsList from './TopicsList'
import TopicsHeader from './TopicsHeader'
import TopicsExecute from './TopicsExecute'
import { mapGetters } from 'vuex'

export default {
  name: 'Topics',
  computed: mapGetters({
    topics: 'filteredTopics'
  }),
  components: {
    'mt-topics-list': TopicsList,
    'mt-topics-header': TopicsHeader,
    'mt-topics-execute': TopicsExecute
  },
  created () {
    this.$store.dispatch('loadTopics')
  }
}
</script>
