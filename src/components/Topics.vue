<template>
  <div>
    <mt-topics-execute></mt-topics-execute>
    <mt-topics-header></mt-topics-header>
    <mt-topics-list></mt-topics-list>
  </div>
</template>

<script>
import TopicsList from './TopicsList'
import TopicsHeader from './TopicsHeader'
import TopicsExecute from './TopicsExecute'

export default {
  name: 'Topics',
  components: {
    'mt-topics-list': TopicsList,
    'mt-topics-header': TopicsHeader,
    'mt-topics-execute': TopicsExecute
  }
}
</script>
