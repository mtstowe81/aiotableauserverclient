# aiotableauserverclient
Implementation of tableauserverclient API using asynio following the API conventions of the `tableauserverclient` library implemented by Tableau.

Using the `/subscriptions` endpoint of Tableau as an example typical usage, per their documentation is as follows.

```
import tableauserverclient as TSC

tableau_auth = TSC.TableauAuth('USERNAME', 'PASSWORD', site_id='CONTENTURL')
server = TSC.Server('https://SERVER_URL', use_server_version=True)
server.auth.sign_in(tableau_auth)

# Create the target (content) of the subscription with its ID and type.
# ID can be obtained by calling workbooks.get() or views.get().
target = TSC.Target('c7a9327e-1cda-4504-b026-ddb43b976d1d', 'workbook')

# Store the schedule ID and user ID.
# IDs can be obtained by calling schedules.get() and users.get().
schedule_id = 'b60b4efd-a6f7-4599-beb3-cb677e7abac1'
user_id = '28ce5884-ed38-49a9-aa10-8f5fbd59bbf6'

# Create the new SubscriptionItem object with variables from above.
new_sub = TSC.SubscriptionItem('My Subscription', schedule_id, user_id, target)

# (Optional) Set other fields. Any of these can be added or removed.
new_sub.attach_image = False
new_sub.attach_pdf = True
new_sub.message = "You have an alert!"
new_sub.page_orientation = TSC.PDFRequestOptions.Orientation.Landscape
new_sub.page_size_option = TSC.PDFRequestOptions.PageType.B4
new_sub.send_if_view_empty = True

# Create the new subscription on the site you are logged in.
new_sub = server.subscriptions.create(new_sub)
```

This works perfectly well when running automation, however when integration Tableu interactions into a web server it is preferred to utilize asyncio to ensure throughput.

In such cases an async pattern can be applied when following the above convention and using the async implementation style provided in our example.  Instead of creating the `tableauserverclient.Server` instance used above, in the below you would create an instance of `aiotableauserverclient.TableauClientAsync` allowing you to use the same conventions as above, except introducing `await` into your server interactions.  This library is designed to take full advantage of the `tableauserverclient` package's entities, serder, etc... so that it is only replacing underlying networking operations.

This maintains an almost identical experience to the original library, except introducing `async/await`.


```
import aiotableauserverclient as TSC
server = TSC.TableauClientAsync('https://SERVER_URL','USERNAME', 'PASSWORD', site_id='CONTENTURL', api_ver='API_VERSION')

# Initialize the client connection and auth.
await server.sign_in()

# Create the target (content) of the subscription with its ID and type.
# ID can be obtained by calling workbooks.get() or views.get().
target = TSC.Target('c7a9327e-1cda-4504-b026-ddb43b976d1d', 'workbook')

# Store the schedule ID and user ID.
# IDs can be obtained by calling schedules.get() and users.get().
schedule_id = 'b60b4efd-a6f7-4599-beb3-cb677e7abac1'
user_id = '28ce5884-ed38-49a9-aa10-8f5fbd59bbf6'

# Create the new SubscriptionItem object with variables from above.
new_sub = TSC.SubscriptionItem('My Subscription', schedule_id, user_id, target)

# (Optional) Set other fields. Any of these can be added or removed.
new_sub.attach_image = False
new_sub.attach_pdf = True
new_sub.message = "You have an alert!"
new_sub.page_orientation = TSC.PDFRequestOptions.Orientation.Landscape
new_sub.page_size_option = TSC.PDFRequestOptions.PageType.B4
new_sub.send_if_view_empty = True

# Create the new subscription on the site you are logged in.
new_sub = await server.subscriptions.create(new_sub)

# Cleanup the client connection/etc
await server.close()
```