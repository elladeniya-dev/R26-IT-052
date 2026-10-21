---
tags:
- sentence-transformers
- sentence-similarity
- feature-extraction
- dense
- generated_from_trainer
- dataset_size:15712
- loss:TripletLoss
base_model: sentence-transformers/all-MiniLM-L6-v2
widget:
- source_sentence: 'Customer fashion preference based on previous purchases. Preferred
    product types: Trousers. Preferred product groups: Garment Lower body. Preferred
    colors: Black. Preferred appearances: Solid. Preferred sections: Womens Everyday
    Basics. Preferred garment groups: Jersey Basic.'
  sentences:
  - 'Product name: Harem trousers. Product type: Trousers. Product group: Garment
    Lower body. Color: Black. Appearance: Solid. Department: Jersey Basic. Section:
    Womens Everyday Basics. Garment group: Jersey Basic. Description: Harem trousers
    in jersey with elastication at the waist and hems..'
  - 'Product name: Topi dress J. Product type: Dress. Product group: Garment Full
    body. Color: Black. Appearance: Solid. Department: Dresses. Section: Divided Collection.
    Garment group: Dresses Ladies. Description: .'
  - 'Product name: R-NECK SS BASIC FIT. Product type: T-shirt. Product group: Garment
    Upper body. Color: Black. Appearance: Solid. Department: Jersey Basic. Section:
    Men Underwear. Garment group: Jersey Basic. Description: Round-necked T-shirt
    in organic cotton jersey..'
- source_sentence: 'Customer fashion preference based on previous purchases. Preferred
    product types: Socks. Preferred product groups: Socks & Tights. Preferred colors:
    Black. Preferred appearances: Solid. Preferred sections: Womens Nightwear, Socks
    & Tigh. Preferred garment groups: Socks and Tights.'
  sentences:
  - 'Product name: 30p pins. Product type: Hair clip. Product group: Accessories.
    Color: Black. Appearance: Solid. Department: Hair Accessories. Section: Womens
    Small accessories. Garment group: Accessories. Description: Metal hair grips.
    Length 5 cm..'
  - 'Product name: Maggie RW tapered. Product type: Trousers. Product group: Garment
    Lower body. Color: Greyish Beige. Appearance: Solid. Department: Trouser. Section:
    Womens Everyday Collection. Garment group: Trousers. Description: .'
  - 'Product name: Tuva LS TPP. Product type: Top. Product group: Garment Upper body.
    Color: White. Appearance: Solid. Department: Tops Fancy Jersey. Section: Divided
    Collection. Garment group: Jersey Fancy. Description: Fitted top in ribbed jersey
    with a square neckline and long puff sleeves..'
- source_sentence: 'Customer fashion preference based on previous purchases. Preferred
    product types: Sweater. Preferred product groups: Garment Upper body. Preferred
    colors: Red. Preferred appearances: Melange. Preferred sections: Divided Collection.
    Preferred garment groups: Knitwear.'
  sentences:
  - 'Product name: IZZY loose tee (1). Product type: T-shirt. Product group: Garment
    Upper body. Color: Black. Appearance: Melange. Department: Ladies Sport Bras.
    Section: Ladies H&M Sport. Garment group: Jersey Fancy. Description: .'
  - 'Product name: Alex fancy basic tee. Product type: T-shirt. Product group: Garment
    Upper body. Color: White. Appearance: Colour blocking. Department: Baby Boy Jersey
    Fancy. Section: Baby Boy. Garment group: Jersey Fancy. Description: T-shirt in
    soft cotton jersey with buttons on one shoulder..'
  - 'Product name: Anita Tank (1). Product type: Vest top. Product group: Garment
    Upper body. Color: Black. Appearance: Solid. Department: Basic 1. Section: Divided
    Basics. Garment group: Jersey Basic. Description: Fitted vest top in soft jersey..'
- source_sentence: 'Customer fashion preference based on previous purchases. Preferred
    product types: Blouse. Preferred product groups: Garment Upper body. Preferred
    colors: Unknown. Preferred appearances: Unknown. Preferred sections: Womens Tailoring.
    Preferred garment groups: Blouses.'
  sentences:
  - 'Product name: Heavy jsy long leg. Product type: Leggings/Tights. Product group:
    Garment Lower body. Color: Black. Appearance: Contrast. Department: Basic 1. Section:
    Divided Basics. Garment group: Jersey Basic. Description: Leggings in extra sturdy
    jersey with an elasticated waist..'
  - 'Product name: 2- PACK. Product type: T-shirt. Product group: Garment Upper body.
    Color: White. Appearance: Solid. Department: Jersey Basic. Section: Womens Everyday
    Basics. Garment group: Jersey Basic. Description: Short-sleeved tops in organic
    cotton jersey with a round neckline..'
  - 'Product name: R-NECK SS SLIM FIT. Product type: T-shirt. Product group: Garment
    Upper body. Color: Beige. Appearance: Solid. Department: Light Basic Jersey. Section:
    Men Underwear. Garment group: Jersey Basic. Description: Round-necked T-shirt
    in soft jersey..'
- source_sentence: 'Customer fashion preference based on previous purchases. Preferred
    product types: Trousers. Preferred product groups: Garment Lower body. Preferred
    colors: Blue. Preferred appearances: Denim. Preferred sections: Kids Boy. Preferred
    garment groups: Trousers Denim.'
  sentences:
  - 'Product name: Basic Elliot necklace. Product type: Necklace. Product group: Accessories.
    Color: Silver. Appearance: Solid. Department: Jewellery. Section: Womens Small
    accessories. Garment group: Accessories. Description: Thin metal chain necklace
    with a round pendant..'
  - 'Product name: Barcelona. Product type: Cardigan. Product group: Garment Upper
    body. Color: Yellow. Appearance: Solid. Department: Kids Girl Knitwear. Section:
    Kids Girl. Garment group: Knitwear. Description: Cardigan in textured-knit cotton
    with a round neck, buttons down the front and narrow ribbing at the cuffs and
    hem..'
  - 'Product name: Maggie RW tapered. Product type: Trousers. Product group: Garment
    Lower body. Color: Black. Appearance: Solid. Department: Trouser. Section: Womens
    Everyday Collection. Garment group: Trousers. Description: .'
pipeline_tag: sentence-similarity
library_name: sentence-transformers
metrics:
- cosine_accuracy
model-index:
- name: SentenceTransformer based on sentence-transformers/all-MiniLM-L6-v2
  results:
  - task:
      type: triplet
      name: Triplet
    dataset:
      name: koji fashion validation
      type: koji-fashion-validation
    metrics:
    - type: cosine_accuracy
      value: 0.8518329858779907
      name: Cosine Accuracy
---

# SentenceTransformer based on sentence-transformers/all-MiniLM-L6-v2

This is a [sentence-transformers](https://www.SBERT.net) model finetuned from [sentence-transformers/all-MiniLM-L6-v2](https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2). It maps inputs to a 384-dimensional dense vector space and can be used for semantic textual similarity, semantic search, paraphrase mining, classification, clustering, and more.

## Model Details

### Model Description
- **Model Type:** Sentence Transformer
- **Base model:** [sentence-transformers/all-MiniLM-L6-v2](https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2) <!-- at revision 1110a243fdf4706b3f48f1d95db1a4f5529b4d41 -->
- **Maximum Sequence Length:** 256 tokens
- **Output Dimensionality:** 384 dimensions
- **Similarity Function:** Cosine Similarity
- **Supported Modality:** Text
<!-- - **Training Dataset:** Unknown -->
<!-- - **Language:** Unknown -->
<!-- - **License:** Unknown -->

### Model Sources

- **Documentation:** [Sentence Transformers Documentation](https://sbert.net)
- **Repository:** [Sentence Transformers on GitHub](https://github.com/huggingface/sentence-transformers)
- **Hugging Face:** [Sentence Transformers on Hugging Face](https://huggingface.co/models?library=sentence-transformers)

### Full Model Architecture

```
SentenceTransformer(
  (0): Transformer({'transformer_task': 'feature-extraction', 'modality_config': {'text': {'method': 'forward', 'method_output_name': 'last_hidden_state'}}, 'module_output_name': 'token_embeddings', 'architecture': 'BertModel'})
  (1): Pooling({'embedding_dimension': 384, 'pooling_mode': 'mean', 'include_prompt': True})
  (2): Normalize({'module_input_name': 'sentence_embedding', 'module_output_name': 'sentence_embedding'})
)
```

## Usage

### Direct Usage (Sentence Transformers)

First install the Sentence Transformers library:

```bash
pip install -U sentence-transformers
```
Then you can load this model and run inference.
```python
from sentence_transformers import SentenceTransformer

# Download from the 🤗 Hub
model = SentenceTransformer("sentence_transformers_model_id")
# Run inference
sentences = [
    'Customer fashion preference based on previous purchases. Preferred product types: Trousers. Preferred product groups: Garment Lower body. Preferred colors: Blue. Preferred appearances: Denim. Preferred sections: Kids Boy. Preferred garment groups: Trousers Denim.',
    'Product name: Barcelona. Product type: Cardigan. Product group: Garment Upper body. Color: Yellow. Appearance: Solid. Department: Kids Girl Knitwear. Section: Kids Girl. Garment group: Knitwear. Description: Cardigan in textured-knit cotton with a round neck, buttons down the front and narrow ribbing at the cuffs and hem..',
    'Product name: Maggie RW tapered. Product type: Trousers. Product group: Garment Lower body. Color: Black. Appearance: Solid. Department: Trouser. Section: Womens Everyday Collection. Garment group: Trousers. Description: .',
]
embeddings = model.encode(sentences)
print(embeddings.shape)
# [3, 384]

# Get the similarity scores for the embeddings
similarities = model.similarity(embeddings, embeddings)
print(similarities)
# tensor([[ 1.0000,  0.9952, -0.9875],
#         [ 0.9952,  1.0000, -0.9842],
#         [-0.9875, -0.9842,  1.0000]])
```
<!--
### Direct Usage (Transformers)

<details><summary>Click to see the direct usage in Transformers</summary>

</details>
-->

<!--
### Downstream Usage (Sentence Transformers)

You can finetune this model on your own dataset.

<details><summary>Click to expand</summary>

</details>
-->

<!--
### Out-of-Scope Use

*List how the model may foreseeably be misused and address what users ought not to do with the model.*
-->

## Evaluation

### Metrics

#### Triplet

* Dataset: `koji-fashion-validation`
* Evaluated with [<code>TripletEvaluator</code>](https://sbert.net/docs/package_reference/sentence_transformer/evaluation.html#sentence_transformers.sentence_transformer.evaluation.TripletEvaluator)

| Metric              | Value      |
|:--------------------|:-----------|
| **cosine_accuracy** | **0.8518** |

<!--
## Bias, Risks and Limitations

*What are the known or foreseeable issues stemming from this model? You could also flag here known failure cases or weaknesses of the model.*
-->

<!--
### Recommendations

*What are recommendations with respect to the foreseeable issues? For example, filtering explicit content.*
-->

## Training Details

### Training Dataset

#### Unnamed Dataset

* Size: 15,712 training samples
* Columns: <code>sentence_0</code>, <code>sentence_1</code>, and <code>sentence_2</code>
* Approximate statistics based on the first 100 samples:
  |          | sentence_0                                                                          | sentence_1                                                                          | sentence_2                                                                          |
  |:---------|:------------------------------------------------------------------------------------|:------------------------------------------------------------------------------------|:------------------------------------------------------------------------------------|
  | type     | string                                                                              | string                                                                              | string                                                                              |
  | modality | text                                                                                | text                                                                                | text                                                                                |
  | details  | <ul><li>min: 44 tokens</li><li>mean: 64.93 tokens</li><li>max: 126 tokens</li></ul> | <ul><li>min: 57 tokens</li><li>mean: 82.86 tokens</li><li>max: 142 tokens</li></ul> | <ul><li>min: 57 tokens</li><li>mean: 85.03 tokens</li><li>max: 120 tokens</li></ul> |
* Samples:
  | sentence_0                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          | sentence_1                                                                                                                                                                                                                                                                                                                                                                                                                                                                     | sentence_2                                                                                                                                                                                                                                                                                                                                                                                                                                              |
  |:------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|:-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|:--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
  | <code>Customer fashion preference based on previous purchases. Preferred product types: T-shirt. Preferred product groups: Garment Upper body. Preferred colors: Red. Preferred appearances: Placement print. Preferred sections: Divided Collection. Preferred garment groups: Jersey Fancy.</code>                                                                                                                                                                                                                                                                                | <code>Product name: Mandrill SS Embro. Product type: Top. Product group: Garment Upper body. Color: Dark Blue. Appearance: Embroidery. Department: Tops Fancy Jersey. Section: Divided Collection. Garment group: Jersey Fancy. Description: Short, wide top in lightweight sweatshirt fabric with appliqués at the top, dropped shoulders and short, wide sleeves. Raw, roll edges at the sleeves and hem..</code>                                                            | <code>Product name: Twiggy padded softbra.. Product type: Bra. Product group: Underwear. Color: Other Purple. Appearance: Lace. Department: Expressive Lingerie. Section: Womens Lingerie. Garment group: Under-, Nightwear. Description: Soft, non-wired lace bra with removable inserts that give the bust a natural shape and light support. Adjustable double shoulder straps and a hook-and-eye fastening at the back..</code>                     |
  | <code>Customer fashion preference based on previous purchases. Preferred product types: Underwear bottom, Other accessories, Night gown, Earring, Trousers. Preferred product groups: Underwear, Accessories, Garment Lower body, Nightwear. Preferred colors: Black, Gold, White. Preferred appearances: Solid, All over pattern, Lace, Check, Contrast. Preferred sections: Womens Lingerie, Womens Small accessories, Womens Nightwear, Socks & Tigh, Womens Tailoring, Divided Basics. Preferred garment groups: Under-, Nightwear, Accessories, Trousers, Jersey Basic.</code> | <code>Product name: Hazel playsuit. Product type: Trousers. Product group: Garment Lower body. Color: Red. Appearance: All over pattern. Department: Trouser. Section: Womens Everyday Collection. Garment group: Trousers. Description: Playsuit in a viscose weave with a V-neck, wrapover front with a concealed hook-and-eye fastener and 3/4-length sleeves with ties at the cuffs. Elasticated seam at the waist, side pockets and a frill at the hems. Unlined..</code> | <code>Product name: SANDY Fleece Beanie. Product type: Hat/beanie. Product group: Accessories. Color: Light Pink. Appearance: Solid. Department: Kids Girl Big Acc. Section: Kids Outerwear. Garment group: Accessories. Description: Hat in thermal fleece with a contrasting colour trim at the hem..</code>                                                                                                                                          |
  | <code>Customer fashion preference based on previous purchases. Preferred product types: Leggings/Tights, Trousers, Top, T-shirt. Preferred product groups: Garment Lower body, Garment Upper body. Preferred colors: White, Other Pink, Light Blue. Preferred appearances: All over pattern, Denim, Solid. Preferred sections: Girls Underwear & Basics, Kids Girl. Preferred garment groups: Jersey Basic, Trousers Denim, Knitwear.</code>                                                                                                                                        | <code>Product name: FREJA. Product type: T-shirt. Product group: Garment Upper body. Color: Light Grey. Appearance: All over pattern. Department: Kids Girl Jersey Basic. Section: Girls Underwear & Basics. Garment group: Jersey Basic. Description: Long-sleeved tops in organic cotton jersey..</code>                                                                                                                                                                     | <code>Product name: BEN basic crewneck SB. Product type: Sweater. Product group: Garment Upper body. Color: Light Blue. Appearance: Solid. Department: Kids Boy Jersey Basic. Section: Boys Underwear & Basics. Garment group: Jersey Basic. Description: Long-sleeved top in sweatshirt fabric made from a cotton blend with ribbing around the neckline, cuffs and hem. Soft brushed inside. The cotton content of the sweatshirt is organic..</code> |
* Loss: [<code>TripletLoss</code>](https://sbert.net/docs/package_reference/sentence_transformer/losses.html#tripletloss) with these parameters:
  ```json
  {
      "distance_metric": "TripletDistanceMetric.EUCLIDEAN",
      "triplet_margin": 5
  }
  ```

### Training Hyperparameters
#### Non-Default Hyperparameters

- `per_device_train_batch_size`: 16
- `num_train_epochs`: 1
- `per_device_eval_batch_size`: 16
- `multi_dataset_batch_sampler`: round_robin

#### All Hyperparameters
<details><summary>Click to expand</summary>

- `per_device_train_batch_size`: 16
- `num_train_epochs`: 1
- `max_steps`: -1
- `learning_rate`: 5e-05
- `lr_scheduler_type`: linear
- `lr_scheduler_kwargs`: None
- `warmup_steps`: 0
- `optim`: adamw_torch_fused
- `optim_args`: None
- `weight_decay`: 0.0
- `adam_beta1`: 0.9
- `adam_beta2`: 0.999
- `adam_epsilon`: 1e-08
- `optim_target_modules`: None
- `gradient_accumulation_steps`: 1
- `average_tokens_across_devices`: True
- `max_grad_norm`: 1
- `label_smoothing_factor`: 0.0
- `bf16`: False
- `fp16`: False
- `bf16_full_eval`: False
- `fp16_full_eval`: False
- `tf32`: None
- `gradient_checkpointing`: False
- `gradient_checkpointing_kwargs`: None
- `torch_compile`: False
- `torch_compile_backend`: None
- `torch_compile_mode`: None
- `use_liger_kernel`: False
- `liger_kernel_config`: None
- `use_cache`: False
- `neftune_noise_alpha`: None
- `torch_empty_cache_steps`: None
- `auto_find_batch_size`: False
- `log_on_each_node`: True
- `logging_nan_inf_filter`: True
- `include_num_input_tokens_seen`: no
- `log_level`: passive
- `log_level_replica`: warning
- `disable_tqdm`: False
- `project`: huggingface
- `trackio_space_id`: None
- `trackio_bucket_id`: None
- `trackio_static_space_id`: None
- `per_device_eval_batch_size`: 16
- `prediction_loss_only`: True
- `eval_on_start`: False
- `eval_do_concat_batches`: True
- `eval_use_gather_object`: False
- `eval_accumulation_steps`: None
- `include_for_metrics`: []
- `batch_eval_metrics`: False
- `save_only_model`: False
- `save_on_each_node`: False
- `enable_jit_checkpoint`: False
- `push_to_hub`: False
- `hub_private_repo`: None
- `hub_model_id`: None
- `hub_strategy`: every_save
- `hub_always_push`: False
- `hub_revision`: None
- `load_best_model_at_end`: False
- `ignore_data_skip`: False
- `restore_callback_states_from_checkpoint`: False
- `full_determinism`: False
- `seed`: 42
- `data_seed`: None
- `use_cpu`: False
- `accelerator_config`: {'split_batches': False, 'dispatch_batches': None, 'even_batches': True, 'use_seedable_sampler': True, 'non_blocking': False, 'gradient_accumulation_kwargs': None}
- `parallelism_config`: None
- `dataloader_drop_last`: False
- `dataloader_num_workers`: 0
- `dataloader_pin_memory`: True
- `dataloader_persistent_workers`: False
- `dataloader_prefetch_factor`: None
- `dataloader_multiprocessing_context`: None
- `dataloader_in_order`: True
- `remove_unused_columns`: True
- `label_names`: None
- `train_sampling_strategy`: random
- `length_column_name`: length
- `ddp_find_unused_parameters`: None
- `ddp_bucket_cap_mb`: None
- `ddp_broadcast_buffers`: False
- `ddp_static_graph`: None
- `ddp_backend`: None
- `ddp_timeout`: 1800
- `fsdp`: None
- `fsdp_config`: None
- `deepspeed`: None
- `debug`: []
- `skip_memory_metrics`: True
- `do_predict`: False
- `resume_from_checkpoint`: None
- `local_rank`: -1
- `prompts`: None
- `batch_sampler`: batch_sampler
- `multi_dataset_batch_sampler`: round_robin
- `router_mapping`: {}
- `learning_rate_mapping`: {}
- `warmup_ratio`: None

</details>

### Training Logs
| Epoch  | Step | Training Loss | koji-fashion-validation_cosine_accuracy |
|:------:|:----:|:-------------:|:---------------------------------------:|
| 0.2037 | 200  | -             | 0.8411                                  |
| 0.4073 | 400  | -             | 0.8452                                  |
| 0.5092 | 500  | 4.3056        | -                                       |
| 0.6110 | 600  | -             | 0.8518                                  |


### Training Time
- **Training**: 2.0 minutes

### Framework Versions
- Python: 3.13.15
- Sentence Transformers: 6.0.0
- Transformers: 5.16.0
- PyTorch: 2.11.0+cu128
- Accelerate: 1.14.0
- Datasets: 5.0.1
- Tokenizers: 0.23.1

## Additional Resources

- [Training and Finetuning Embedding Models with Sentence Transformers](https://huggingface.co/blog/train-sentence-transformers): the end-to-end guide for training or finetuning Sentence Transformer models.
- [Introduction to Matryoshka Embedding Models](https://huggingface.co/blog/matryoshka): variable-size embeddings that can be truncated with minimal quality loss.
- [Binary and Scalar Embedding Quantization for Significantly Faster & Cheaper Retrieval](https://huggingface.co/blog/embedding-quantization): post-training compression of embedding vectors.
- [Multimodal Embedding & Reranker Models with Sentence Transformers](https://huggingface.co/blog/multimodal-sentence-transformers): use text, image, audio, and video models through the same API.
- [Training and Finetuning Multimodal Embedding & Reranker Models with Sentence Transformers](https://huggingface.co/blog/train-multimodal-sentence-transformers): train multimodal embedding models, with a Visual Document Retrieval walkthrough.

## Citation

### BibTeX

#### Sentence Transformers
```bibtex
@inproceedings{reimers-2019-sentence-bert,
    title = "Sentence-BERT: Sentence Embeddings using Siamese BERT-Networks",
    author = "Reimers, Nils and Gurevych, Iryna",
    booktitle = "Proceedings of the 2019 Conference on Empirical Methods in Natural Language Processing",
    month = "11",
    year = "2019",
    publisher = "Association for Computational Linguistics",
    url = "https://arxiv.org/abs/1908.10084",
}
```

#### TripletLoss
```bibtex
@misc{hermans2017defense,
    title={In Defense of the Triplet Loss for Person Re-Identification},
    author={Alexander Hermans and Lucas Beyer and Bastian Leibe},
    year={2017},
    eprint={1703.07737},
    archivePrefix={arXiv},
    primaryClass={cs.CV}
}
```

<!--
## Glossary

*Clearly define terms in order to be accessible across audiences.*
-->

<!--
## Model Card Authors

*Lists the people who create the model card, providing recognition and accountability for the detailed work that goes into its construction.*
-->

<!--
## Model Card Contact

*Provides a way for people who have updates to the Model Card, suggestions, or questions, to contact the Model Card authors.*
-->