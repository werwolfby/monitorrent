<template>
  <div>
    <mt-topics-header></mt-topics-header>
    <mt-topics-list></mt-topics-list>
  </div>
</template>

<script>
import TopicsList from './TopicsList'
import TopicsHeader from './TopicsHeader'

export default {
  name: 'Topics',
  components: {
    'mt-topics-list': TopicsList,
    'mt-topics-header': TopicsHeader
  }
}
</script>
