export function throwOnError (response) {
    if (response.status >= 500 || (response.status === 400 || response.status === 404)) {
        return response.json().then(result => {
            const error = new Error(result.title)
            error.status = response.status
            error.description = result.description
            throw error
        })
    } else if (response.status >= 300) {
        return response.text().then(result => {
            throw new Error(result)
        })
    }

    return response
}
