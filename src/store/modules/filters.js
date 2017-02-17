export function smartFilter (topics, filterString) {
    function filterValue (value, filterString) {
        return value.display_name.toLowerCase().indexOf(filterString) > -1 ||
              value.tracker.toLowerCase().indexOf(filterString) > -1
    }

    let filterStringParams = filterString.split(' ').filter(e => e).map(e => e.toLowerCase())
    return topics.filter(t => filterStringParams.every(p => filterValue(t, p)))
}

const orderKeys = ['display_name', 'last_update']

export function smartOrder (topics, order) {
    function getKey (topic, order) {
        let orderValue = topic[order]
        if (order === 'last_update') {
            orderValue = new Date(orderValue || 32503680000000)
        }

        return orderValue
    }

    function compare (a, b, order) {
        let reverse = 1

        if (order.substring(0, 1) === '-') {
            reverse = -1
            order = order.substring(1)
        }

        const aKey = getKey(a, order)
        const bKey = getKey(b, order)

        if (aKey < bKey) {
            return -1 * reverse
        }

        if (aKey > bKey) {
            return 1 * reverse
        }

        return 0
    }

    const filteredOrder = order.substring(0, 1) === '-' ? order.substring(1) : order
    const index = orderKeys.indexOf(filteredOrder)
    const orderList = [order, ...orderKeys.slice(0, index), ...orderKeys.slice(index + 1)]

    return [...topics].sort((a, b) => orderList.reduce((acc, order) => acc === 0 ? compare(a, b, order) : acc, 0))
}
