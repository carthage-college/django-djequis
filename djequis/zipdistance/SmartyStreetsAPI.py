import os
from smartystreets_python_sdk import StaticCredentials, exceptions, ClientBuilder
from smartystreets_python_sdk.us_street import Lookup

#  Find info at https://smartystreets.com/docs/sdk/python


def run():
	auth_id = "adb734b8-b557-1c42-d9fb-012cc77a036a"
	auth_token = "3rhZrunJZDj1QSW3K8si"

	# We recommend storing your secret keys in environment variables instead---it's safer!
	# auth_id = os.environ['SMARTY_AUTH_ID']
	# auth_token = os.environ['SMARTY_AUTH_TOKEN']

	credentials = StaticCredentials(auth_id, auth_token)

	client = ClientBuilder(credentials).build_us_street_api_client()
	# client = ClientBuilder(credentials).with_proxy('localhost:8080', 'user', 'password').build_us_street_api_client()
	# Uncomment the line above to try it with a proxy instead

	lookup = Lookup()
	lookup.street = "1600 Amphitheatre Pkwy"
	lookup.city = "Mountain View"
	lookup.state = "CA"

	try:
		client.send_lookup(lookup)
	except exceptions.SmartyException as err:
		print(err)
		return

	result = lookup.result

	if not result:
		print("No candidates. This means the address is not valid.")
		return

	first_candidate = result[0]

	print("Address is valid. (There is at least one candidate)\n")
	print("ZIP Code: " + first_candidate.components.zipcode)
	print("County: " + first_candidate.metadata.county_name)
	print("Latitude: {}".format(first_candidate.metadata.latitude))
	print("Longitude: {}".format(first_candidate.metadata.longitude))


if __name__ == "__main__":
	run()