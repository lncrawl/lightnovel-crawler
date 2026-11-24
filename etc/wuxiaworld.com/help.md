Install the packages required:

```
pip install grpcio-tools
pip install pyease-grpc >= 1.8
pip install requests
```

Wuxiaworld protobuf pipeline.

    python wuxia_proto.py scrape   [URL] [-f _proto] [-e .ts] [-o DIR] [-j 8]
    python wuxia_proto.py generate [--native-maps] [--no-optional] [-v]
    python wuxia_proto.py dump     [--py] [--json] [--pretty]
    python wuxia_proto.py all      [URL]            # scrape + generate + dump --py

scrape    pull the original TypeScript from the site's source maps (like DevTools > Sources)
generate  TypeScript -> proto_temp/*.proto + proto_temp/wuxia.proto (imports everything)
dump      compile wuxia.proto with pyease_grpc -> wuxiacom_proto.py (and/or wuxia.json)


All paths are relative to this script, not to the current directory.

To get wuxiacom_proto.py that contain WUXIWORLD_PROTO variable, run this command:
```
python wuxia_proto.py all
```