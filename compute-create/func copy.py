# import io
# import json
# import logging
# import oci

# from fdk import response


# # def handler(ctx, data: io.BytesIO = None):
# #     name = "World"
# #     try:
# #         body = json.loads(data.getvalue())
# #         name = body.get("name")
# #     except (Exception, ValueError) as ex:
# #         logging.getLogger().info('error parsing json payload: ' + str(ex))

# #     logging.getLogger().info("Inside Python Hello World function")
# #     return response.Response(
# #         ctx, response_data=json.dumps(
# #             {"message": "ctx {0}".format(ctx)}),
# #         headers={"Content-Type": "application/json"}
# #     )



# # def handler(ctx, data: io.BytesIO=None):
# #     name = "World"
# #     try:
# #         body = json.loads(data.getvalue())
# #         name = body.get("name")
# #     except (Exception, ValueError) as ex:
# #         print(str(ex))
# #     x = response_data=json.dumps(
# #             {"Message": "Hello {0}".format(name),
# #             "ctx.Config" : dict(ctx.Config()),
# #             "ctx.Headers" : ctx.Headers(),
# #             "ctx.AppID" : ctx.AppID(),
# #             "ctx.FnID" : ctx.FnID(),
# #             "ctx.CallID" : ctx.CallID(),
# #             "ctx.Format" : ctx.Format(),
# #             "ctx.Deadline" : ctx.Deadline(),
# #             "ctx.RequestURL": ctx.RequestURL(),
# #             "ctx.Method": ctx.Method()},
# #             sort_keys=True, indent=4)
# #     logging.getLogger().info("info : {} ".format(x))
# #     return response.Response(
# #         ctx,x,headers={"Content-Type": "application/json"}
# #     )


# def handler(ctx, data: io.BytesIO=None):
#     signer = oci.auth.signers.get_resource_principals_signer()
#     object_name = bucket_name = namespace = ordsbaseurl = schema = dbuser = dbpwd = ""
#     # try:
#     #     cfg = ctx.Config()
#     #     input_bucket = cfg["INPUT_BUCKET"]
#     #     processed_bucket = cfg["PROCESSED_BUCKET"]
#     #     ordsbaseurl = cfg["ORDS_BASE_URL"]
#     #     schema = cfg["DB_SCHEMA"]
#     #     dbuser = cfg["DB_USER"]
#     #     dbpwd = cfg["DBPWD_CIPHER"]
#     # except Exception as e:
#     #     print('Missing function parameters: bucket_name, ordsbaseurl, schema, dbuser, dbpwd', flush=True)
#     #     raise
#     try:
#         body = json.loads(data.getvalue())
#         # print("INFO - Event ID {} received".format(body["eventID"]), flush=True)
#         # print("INFO - Object name: " + body["data"]["resourceName"], flush=True)
#         # object_name = body["data"]["resourceName"]
#         # print("INFO - Bucket name: " + body["data"]["additionalDetails"]["bucketName"], flush=True)
#         # # if body["data"]["additionalDetails"]["bucketName"] != input_bucket:
#         # #     raise ValueError("Event Bucket name error")
#         # print("INFO - Namespace: " + body["data"]["additionalDetails"]["namespace"], flush=True)
#         # namespace = body["data"]["additionalDetails"]["namespace"]

#         print(body)
#     except Exception as e:
#         print('ERROR: {}'.format(e), flush=True)

#     return response.Response(
#             ctx, response_data=json.dumps(
#                 {"message": "bla"}),
#             headers={"Content-Type": "application/json"}
#         )