<template>
  <div>
    <mt-topics-execute :loading="loading" :has_topics='topics.length > 0' :execute='last_execute'></mt-topics-execute>
    <mt-topics-header :filter="filter" :order="order" @change-filter="setFilter" @change-order="setOrder"></mt-topics-header>
    <mt-topics-list :topics="topics" :loading="loading"></mt-topics-list>
  </div>
</template>

<script>
import TopicsList from './TopicsList'
import TopicsHeader from './TopicsHeader'
import TopicsExecute from './TopicsExecute'
import types from '../../store/types'
import { mapGetters, mapState } from 'vuex'

export default {
  name: 'Topics',
  computed: {
    ...mapGetters({
      topics: 'filteredTopics'
    }),
    ...mapState({
      loading: state => state.topics.loading,
      last_execute: state => state.topics.last_execute,
      filter: state => state.topics.filterString,
      order: state => state.topics.order
    })
  },
  components: {
    'mt-topics-list': TopicsList,
    'mt-topics-header': TopicsHeader,
    'mt-topics-execute': TopicsExecute
  },
  created () {
    this.$store.dispatch('loadTopics')
  },
  methods: {
    setFilter (value) {
      this.$store.commit(types.SET_FILTER_STRING, { value })
    },
    setOrder (order) {
      this.$store.commit(types.SET_ORDER, { order })
    }
  }
}
</script>
