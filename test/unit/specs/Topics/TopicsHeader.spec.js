import Vue from 'vue'
import TopicsHeader from 'src/components/Topics/TopicsHeader'

describe('TopicsHeader.vue', () => {
  it('should render correct content', () => {
    const Contructor = Vue.extend(TopicsHeader)
    const vm = new Contructor().$mount()
    expect(vm.$el.querySelector('#filter')).to.not.be.null
  })
})
